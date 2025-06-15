# manager/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

# --- ユーザー新規登録フォーム ---
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username',) # ユーザー名のみ

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "ユーザー名"
        self.fields['username'].help_text = "" # ヘルプテキストを削除
        self.fields['password1'].label = "パスワード"
        self.fields['password2'].label = "パスワード（確認用）"
        self.fields['password2'].help_text = "確認のため、もう一度同じパスワードを入力してください。"

# --- ログインフォーム ---
class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "ユーザー名"
        self.fields['password'].label = "パスワード"