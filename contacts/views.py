from django.views.generic import DetailView, View, CreateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages
from .models import Contact
from django.http import JsonResponse
from .forms import ContactForm
from django.urls import reverse_lazy

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
        new_status = request.POST.get('status')
        if new_status in dict(Contact.STATUS_CHOICES):
            contact.status = new_status
            contact.handled_by = request.user
            contact.save()
            messages.success(request, '対応状況を更新しました。')
        return redirect('contact_detail', pk=pk) 

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