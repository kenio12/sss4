from django.core.mail.backends.smtp import EmailBackend as BaseEmailBackend

class CustomEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.connection_params = kwargs.get('connection_params', {})

    def open(self):
        if not self.connection:
            self.connection = self.connection_class(
                self.host, self.port, **self.connection_params)
            if self.use_tls:
                self.connection.starttls()
            if self.username and self.password:
                self.connection.login(self.username, self.password)
        return True