from django.views.generic import DetailView, View, CreateView, ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from .models import Contact
from django.http import JsonResponse
from .forms import ContactForm
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.utils import timezone

class ContactDetailView(UserPassesTestMixin, DetailView):
    model = Contact
    template_name = 'contacts/contact_detail.html'
    context_object_name = 'contact'
    
    def test_func(self):
        # スタッフユーザーのみアクセス可能
        return self.request.user.is_staff 

class ContactUpdateStatusView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff
    
    def post(self, request, pk):
        contact = Contact.objects.get(pk=pk)
        response_text = request.POST.get('response_text')
        
        if response_text:
            contact.status = 'resolved'
            contact.response_text = response_text
            contact.responded_by = request.user
            contact.responded_at = timezone.now()
            contact.save()
            
            messages.success(request, '対応を完了しました。')
        else:
            messages.error(request, '対応内容を入力してください。')
            
        return redirect('contacts:contact_detail', pk=pk) 

class ContactCreateView(CreateView):
    model = Contact
    fields = ['name', 'email', 'subject', 'message']
    template_name = 'contacts/contact_form.html'
    success_url = reverse_lazy('home:terms')
    
    def form_valid(self, form):
        form.instance.source = self.request.POST.get('source', 'other')
        self.object = form.save()
        
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'お問い合わせありがとうございます。'
            })
        
        messages.success(self.request, 'お問い合わせを受け付けました。')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'errors': form.errors,
                'message': '入力内容に問題があります。'
            })
        
        messages.error(self.request, '入力内容に問題があります。')
        return super().form_invalid(form) 

@require_POST
@user_passes_test(lambda u: u.is_staff)
def update_status(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    contact.status = 'resolved'  # 'pending' から 'resolved' に変更
    contact.save()
    return JsonResponse({'status': 'success'}) 

class ContactListView(UserPassesTestMixin, ListView):
    model = Contact
    template_name = 'contacts/contact_list.html'
    context_object_name = 'contacts'
    
    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 未対応のお問い合わせ
        context['pending_contacts'] = Contact.objects.filter(
            status='pending'
        ).order_by('-created_at')
        
        # 対応済みのお問い合わせ
        context['completed_contacts'] = Contact.objects.filter(
            status='resolved'  # または 'completed' など、対応済みを示すステータス
        ).order_by('-created_at')
        
        return context 