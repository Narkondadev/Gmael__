import os
import json
import datetime
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
import imaplib
import email

from apps.core.forms import PINForm, AppPasswordForm
from apps.core.services.pin_service import validate_pin, generate_pin
from apps.core.services.email_service import get_inbox_by_pin, check_expiry
from apps.core.services.gmail_service import fetch_live_emails
from apps.core.models import SharedInbox

# OAuth logic removed in favor of App Password method

def search_email(request):
    """Homepage view to enter PIN and view the inbox"""
    context = {'form': PINForm()}
    
    if request.method == 'POST':
        form = PINForm(request.POST)
        if form.is_valid():
            pin = form.cleaned_data['pin']
            
            if not validate_pin(pin):
                context['error'] = 'Invalid PIN format.'
                return render(request, 'core/index.html', context)
                
            inbox_obj = get_inbox_by_pin(pin)
            if not inbox_obj:
                context['error'] = 'Invalid PIN.'
                return render(request, 'core/index.html', context)
                
            if check_expiry(inbox_obj):
                context['error'] = 'This link has expired.'
                return render(request, 'core/index.html', context)

            if not inbox_obj.is_active:
                context['error'] = 'This PIN has been deactivated.'
                return render(request, 'core/index.html', context)
                
            target_sender = form.cleaned_data['target_email']
                
            # Fetch live emails over Google API - passing the TARGET SENDER and limiting to top 5
            context['is_loading'] = True 
            live_emails = fetch_live_emails(inbox_obj, limit=5, domain=target_sender)
            
            context['inbox'] = inbox_obj
            context['emails'] = live_emails
        else:
            context['form'] = form

    return render(request, 'core/index.html', context)

def add_inbox_view(request):
    """Admin view to add a new Gmail inbox using App Password"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('client_login')
    
    if request.method == 'POST':
        form = AppPasswordForm(request.POST)
        if form.is_valid():
            email_address = form.cleaned_data['email_address']
            app_password = form.cleaned_data['app_password'].replace(" ", "") # Remove spaces
            
            # Generate unique PIN
            pin = generate_pin()
            while SharedInbox.objects.filter(pin=pin).exists():
                pin = generate_pin()
            
            # Default expiry 30 days
            expiry_date = datetime.date.today() + datetime.timedelta(days=30)
            
            # Save to database
            inbox = SharedInbox.objects.create(
                email_address=email_address,
                app_password=app_password,
                pin=pin,
                expiry=expiry_date
            )
            
            context = {
                'email_address': email_address,
                'pin': pin
            }
            return render(request, 'core/success.html', context)
    else:
        form = AppPasswordForm()
        
    return render(request, 'core/add_inbox.html', {'form': form})

def dashboard_view(request):
    """Admin Dashboard to view all generated PINs and History"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('client_login')
        
    inboxes = SharedInbox.objects.all().order_by('-created_at')
    return render(request, 'core/dashboard.html', {'inboxes': inboxes})

def toggle_pin_status(request, pk):
    """Endpoint to instantly deactivate or activate a PIN"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('client_login')
        
    try:
        inbox = SharedInbox.objects.get(pk=pk)
        inbox.is_active = not inbox.is_active # Toggle
        inbox.save()
    except SharedInbox.DoesNotExist:
        pass
        
    return redirect('dashboard')

def delete_pin(request, pk):
    """Endpoint to permanently delete a deactivated PIN"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('client_login')
        
    try:
        inbox = SharedInbox.objects.get(pk=pk)
        # Security block: Only allow deletion if it is ALREADY deactivated
        if not inbox.is_active:
            inbox.delete()
    except SharedInbox.DoesNotExist:
        pass
        
    return redirect('dashboard')

def update_domain_filter(request, pk):
    """Endpoint for admin to hard-lock a domain for a specific user"""
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('client_login')
        
    if request.method == 'POST':
        domain = request.POST.get('allowed_domain', '').strip()
        try:
            inbox = SharedInbox.objects.get(pk=pk)
            inbox.allowed_domain = domain if domain else None
            inbox.save()
        except SharedInbox.DoesNotExist:
            pass
            
    return redirect('dashboard')

def client_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

@login_required(login_url='client_login')
def client_settings(request):
    if not request.user.is_superuser:
        return redirect('client_login')
        
    if request.method == 'POST':
        # Handle Username Change
        if 'action' in request.POST and request.POST['action'] == 'update_username':
            new_username = request.POST.get('new_username')
            if new_username and new_username.strip():
                from django.contrib.auth.models import User
                # Make sure no one else took this username
                if not User.objects.exclude(pk=request.user.pk).filter(username=new_username.strip()).exists():
                    request.user.username = new_username.strip()
                    request.user.save()
            return redirect('client_settings')
            
        # Handle Password Change
        elif 'action' in request.POST and request.POST['action'] == 'update_password':
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)  # Keep them logged in
                return redirect('dashboard')
            else:
                return render(request, 'core/settings.html', {'form': form})
                
    # GET request
    form = PasswordChangeForm(request.user)
    return render(request, 'core/settings.html', {'form': form})

def client_logout(request):
    logout(request)
    return redirect('client_login')
