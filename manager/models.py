# manager/models.py

import os
import uuid
import shutil
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver
import ffmpeg
import logging

logger = logging.getLogger(__name__)

# 1. タグモデル
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="タグ名")
    icon = models.CharField(max_length=50, blank=True, verbose_name="アイコン名", help_text="Remix Iconの名前を入力してください (例: ri-restaurant-line)")

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "タグ"
        verbose_name_plural = "タグ一覧"
        ordering = ['name']

# 2. カスタムユーザーモデル
class User(AbstractUser):
    ROLE_CHOICES = (
        ('visitor', '来場者'),
        ('admin', '管理者'),
        ('gacha', 'ガチャ職員'),
        ('signage', 'サイネージ'),
        ('staff', '出し物職員'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='visitor', verbose_name="役割")
    managed_attractions = models.ManyToManyField(
        'Attraction', 
        blank=True, 
        verbose_name="担当出し物", 
        help_text="役割が「出し物職員」の場合に、担当する出し物を設定してください。"
    )

# 3. 出し物モデル
class Attraction(models.Model):
    STATUS_CHOICES = (
        ('available', '空き'),
        ('normal', '普通'),
        ('crowded', '混雑'),
        ('preparing', '準備中'),
        ('soon', '開演間近'),
        ('showing', '上演中'),
        ('closed', '閉店'),
    )
    
    group_name = models.CharField(max_length=100, verbose_name="団体名")
    attraction_name = models.CharField(max_length=100, verbose_name="出し物名")
    description = models.TextField(verbose_name="紹介文", blank=True)
    video_file = models.FileField(upload_to='videos/originals/', blank=True, null=True, verbose_name="紹介動画ファイル", help_text="MP4などの動画ファイルをアップロードしてください。")
    hls_playlist = models.CharField(max_length=255, blank=True, null=True, verbose_name="HLS再生リストパス")
    tags = models.ManyToManyField('Tag', blank=True, verbose_name="タグ")
    
    capacity = models.PositiveIntegerField(verbose_name="収容人数")
    current_visitors = models.PositiveIntegerField(default=0, verbose_name="現在の人数（並んでいる人を含む）")
    total_visitors = models.PositiveIntegerField(default=0, verbose_name="累計来場者数")

    is_theater = models.BooleanField(default=False, verbose_name="演劇フラグ")
    start_time = models.DateTimeField(verbose_name="開演時間", null=True, blank=True)
    end_time = models.DateTimeField(verbose_name="閉演時間", null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name="現在の状態", default='available')
    likes_count = models.PositiveIntegerField(default=0, verbose_name="高評価数")
    
    entry_qr_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    exit_qr_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return self.attraction_name

    def save(self, *args, **kwargs):
        old_instance = self.__class__.objects.filter(pk=self.pk).first()
        super().save(*args, **kwargs)

        video_updated = False
        # 更新時、かつファイルが変更された場合
        if old_instance and self.video_file != old_instance.video_file:
            video_updated = True
            # 古い元の動画ファイルとHLSフォルダを削除
            if old_instance.video_file and os.path.exists(old_instance.video_file.path):
                os.remove(old_instance.video_file.path)
            if old_instance.hls_playlist:
                old_hls_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', str(old_instance.id))
                if os.path.isdir(old_hls_dir):
                    shutil.rmtree(old_hls_dir)
        # 新規作成時
        elif not old_instance and self.video_file:
            video_updated = True

        # 新しい動画が設定されていればHLS変換を実行
        if self.video_file and video_updated:
            input_path = self.video_file.path
            output_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', str(self.id))
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, 'playlist.m3u8')
            
            try:
                (
                    ffmpeg
                    .input(input_path)
                    .output(output_path, format='hls', hls_time=10, hls_list_size=0,
                            hls_segment_filename=os.path.join(output_dir, 'segment%03d.ts'),
                            vcodec='libx264', acodec='aac', preset='veryfast')
                    .run(cmd='ffmpeg', capture_stdout=True, capture_stderr=True, overwrite_output=True)
                )
                self.hls_playlist = os.path.join('videos', 'hls', str(self.id), 'playlist.m3u8')
                self.__class__.objects.filter(pk=self.pk).update(hls_playlist=self.hls_playlist)
            except ffmpeg.Error as e:
                logger.error(f"Error during HLS conversion for attraction ID {self.pk}:")
                logger.error(f"FFmpeg stdout: {e.stdout.decode('utf8', errors='ignore')}")
                logger.error(f"FFmpeg stderr: {e.stderr.decode('utf8', errors='ignore')}")
                self.hls_playlist = None
                self.__class__.objects.filter(pk=self.pk).update(hls_playlist=self.hls_playlist)
        # 動画ファイルがクリアされた場合
        elif old_instance and not self.video_file and old_instance.video_file:
             # 古い元の動画ファイルとHLSフォルダを削除
            if old_instance.video_file and os.path.exists(old_instance.video_file.path):
                os.remove(old_instance.video_file.path)
            if old_instance.hls_playlist:
                old_hls_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', str(old_instance.id))
                if os.path.isdir(old_hls_dir):
                    shutil.rmtree(old_hls_dir)
            self.hls_playlist = None
            self.__class__.objects.filter(pk=self.pk).update(hls_playlist=None)


# 4. 高評価モデル
class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ユーザー")
    attraction = models.ForeignKey(Attraction, on_delete=models.CASCADE, verbose_name="出し物")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="評価日時")

    class Meta:
        unique_together = ('user', 'attraction')
        verbose_name = "高評価"
        verbose_name_plural = "高評価一覧"

# 5. ガチャチケットモデル
class GachaTicket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="チケット確認用QRコードの中身")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="所有ユーザー")
    is_used = models.BooleanField(default=False, verbose_name="使用済みフラグ")
    issued_at = models.DateTimeField(auto_now_add=True, verbose_name="発行日時")
    used_at = models.DateTimeField(null=True, blank=True, verbose_name="使用日時")
    used_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='used_tickets', verbose_name="使用を承認した職員")
    
    def __str__(self):
        return f"Ticket for {self.user.username}"
    
    class Meta:
        verbose_name = "ガチャチケット"
        verbose_name_plural = "ガチャチケット一覧"

# 6. ユーザー行動履歴モデル
class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="ユーザー")
    attraction = models.ForeignKey(Attraction, on_delete=models.CASCADE, verbose_name="出し物")
    entry_time = models.DateTimeField(auto_now_add=True, verbose_name="入室時間")
    exit_time = models.DateTimeField(null=True, blank=True, verbose_name="退室時間")
    duration_seconds = models.PositiveIntegerField(null=True, blank=True, verbose_name="滞在時間(秒)")

    def save(self, *args, **kwargs):
        if self.exit_time and self.entry_time:
            # Ensure duration_seconds is positive, though entry_time should always be before exit_time
            duration = self.exit_time - self.entry_time
            self.duration_seconds = max(0, duration.total_seconds())
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "ユーザー行動履歴"
        verbose_name_plural = "ユーザー行動履歴一覧"

# 7. システム全体のログモデル
class SystemLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="日時")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="操作ユーザー")
    action = models.CharField(max_length=255, verbose_name="操作内容")
    details = models.TextField(blank=True, verbose_name="詳細")

    def __str__(self):
        return f"[{self.timestamp}] {self.user}: {self.action}"

    class Meta:
        verbose_name = "システムログ"
        verbose_name_plural = "システムログ一覧"

# 8. シグナルレシーバー
@receiver(post_delete, sender=Attraction)
def delete_attraction_files(sender, instance, **kwargs):
    """出し物が削除されたら、関連する動画ファイルとHLSフォルダを削除する"""
    if instance.video_file and os.path.exists(instance.video_file.path):
        os.remove(instance.video_file.path)

    if instance.hls_playlist:
        hls_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'hls', str(instance.id))
        if os.path.isdir(hls_dir):
            shutil.rmtree(hls_dir)