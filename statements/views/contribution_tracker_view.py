from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal

from ..models import ContributionRoom, Contribution
from ..forms.contribution_forms import ContributionRoomForm, ContributionForm


@login_required
def contribution_tracker(request):
    """Main contribution tracker page"""
    current_year = timezone.now().year
    
    # Get all users
    users = User.objects.all().order_by('username')
    
    # Get all contributions
    contributions = Contribution.objects.select_related('user').all().order_by('-date', '-created_at')
    
    # Calculate stats for each user
    user_stats = {}
    for user in users:
        # Get contribution rooms for current year
        tfsa_room = ContributionRoom.objects.filter(
            user=user,
            account_type='TFSA',
            tax_year=current_year
        ).first()
        
        rrsp_room = ContributionRoom.objects.filter(
            user=user,
            account_type='RRSP',
            tax_year=current_year
        ).first()
        
        # Calculate used amounts (exclude previous year contributions)
        tfsa_used = Contribution.objects.filter(
            user=user,
            account_type='TFSA',
            tax_year='current'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        rrsp_used = Contribution.objects.filter(
            user=user,
            account_type='RRSP',
            tax_year='current'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        user_stats[user.id] = {
            'tfsa_limit': tfsa_room.limit if tfsa_room else Decimal('0.00'),
            'rrsp_limit': rrsp_room.limit if rrsp_room else Decimal('0.00'),
            'tfsa_used': tfsa_used,
            'rrsp_used': rrsp_used,
            'tfsa_remaining': (tfsa_room.limit if tfsa_room else Decimal('0.00')) - tfsa_used,
            'rrsp_remaining': (rrsp_room.limit if rrsp_room else Decimal('0.00')) - rrsp_used,
        }
    
    # Get room history for past years (last 5 years)
    room_history = {}
    has_any_history = False
    for user in users:
        past_years = range(current_year - 1, current_year - 6, -1)  # Last 5 years
        user_history = []
        for year in past_years:
            tfsa_room = ContributionRoom.objects.filter(
                user=user,
                account_type='TFSA',
                tax_year=year
            ).first()
            rrsp_room = ContributionRoom.objects.filter(
                user=user,
                account_type='RRSP',
                tax_year=year
            ).first()
            
            if tfsa_room or rrsp_room:
                user_history.append({
                    'year': year,
                    'tfsa_limit': tfsa_room.limit if tfsa_room else None,
                    'rrsp_limit': rrsp_room.limit if rrsp_room else None,
                })
                has_any_history = True
        room_history[user.id] = user_history
    
    today = timezone.now().date()
    
    context = {
        'users': users,
        'contributions': contributions,
        'user_stats': user_stats,
        'room_history': room_history,
        'has_room_history': has_any_history,
        'current_year': current_year,
        'today': today,
        'previous_year': current_year - 1,
    }
    
    return render(request, 'statements/contribution_tracker.html', context)


@login_required
def edit_user_rooms(request, user_id):
    """Edit user's contribution rooms"""
    user = get_object_or_404(User, id=user_id)
    current_year = timezone.now().year
    
    if request.method == 'POST':
        # Update TFSA room
        tfsa_limit = request.POST.get('tfsa_limit')
        if tfsa_limit:
            room, created = ContributionRoom.objects.get_or_create(
                user=user,
                account_type='TFSA',
                tax_year=current_year,
                defaults={'limit': Decimal(tfsa_limit)}
            )
            if not created:
                room.limit = Decimal(tfsa_limit)
                room.save()
        
        # Update RRSP room
        rrsp_limit = request.POST.get('rrsp_limit')
        if rrsp_limit:
            room, created = ContributionRoom.objects.get_or_create(
                user=user,
                account_type='RRSP',
                tax_year=current_year,
                defaults={'limit': Decimal(rrsp_limit)}
            )
            if not created:
                room.limit = Decimal(rrsp_limit)
                room.save()
        
        messages.success(request, f'Successfully updated contribution rooms for {user.username}')
        return redirect('statements:contribution_tracker')
    
    # Get current rooms
    tfsa_room = ContributionRoom.objects.filter(
        user=user,
        account_type='TFSA',
        tax_year=current_year
    ).first()
    
    rrsp_room = ContributionRoom.objects.filter(
        user=user,
        account_type='RRSP',
        tax_year=current_year
    ).first()
    
    context = {
        'user': user,
        'tfsa_limit': tfsa_room.limit if tfsa_room else Decimal('0.00'),
        'rrsp_limit': rrsp_room.limit if rrsp_room else Decimal('0.00'),
        'current_year': current_year,
    }
    
    return render(request, 'statements/edit_user_rooms.html', context)


@login_required
def add_contribution(request):
    """Add a new contribution"""
    if request.method == 'POST':
        # Handle form submission from main tracker page
        user_id = request.POST.get('user')
        account_type = request.POST.get('account_type')
        amount = request.POST.get('amount')
        date = request.POST.get('date')
        tax_year = request.POST.get('tax_year', 'current')
        
        if user_id and account_type and amount and date:
            try:
                user = User.objects.get(id=user_id)
                contribution = Contribution.objects.create(
                    user=user,
                    account_type=account_type,
                    amount=Decimal(amount),
                    date=date,
                    tax_year=tax_year
                )
                messages.success(
                    request, 
                    f'Successfully logged {contribution.account_type} contribution of ${contribution.amount} for {contribution.user.username}'
                )
                return redirect('statements:contribution_tracker')
            except Exception as e:
                messages.error(request, f'Error creating contribution: {str(e)}')
        else:
            messages.error(request, 'Please fill in all required fields.')
            return redirect('statements:contribution_tracker')
    
    # If GET request, show the add contribution page
    form = ContributionForm(users=User.objects.all())
    return render(request, 'statements/add_contribution.html', {'form': form})


@login_required
def delete_contribution(request, contribution_id):
    """Delete a contribution"""
    contribution = get_object_or_404(Contribution, id=contribution_id)
    
    if request.method == 'POST':
        contribution.delete()
        messages.success(request, 'Successfully deleted contribution')
        return redirect('statements:contribution_tracker')
    
    return redirect('statements:contribution_tracker')
