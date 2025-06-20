## 文化祭混雑状況管理システム - README

**はじめに**

このドキュメントは、「文化祭混雑状況管理システム」の技術的な仕様、使い方、そして今後の開発のための引継ぎ情報をまとめたものです。
本システムは、Djangoフレームワークを基盤として開発されたWebアプリケーションで、文化祭をよりスムーズに、そして楽しく運営することを目的としています。

**このシステムでできること（主なメリット）**

*   **来場者の方へ**: スマートフォン等から、各出し物の現在の混雑具合をリアルタイムで確認できます。また、出し物を体験することでガチャチケットを獲得したり、気に入った出し物を評価（いいね！）したりすることも可能です。これにより、待ち時間の少ない出し物を選んだり、効率的に文化祭を回ったりするのに役立ちます。
*   **出展者・運営者の方へ**: 各出し物の混雑状況を正確に把握し、必要に応じて入場制限などの対策を講じることができます。また、管理画面からは出し物情報の登録・更新、来場者からの評価の確認、QRコードの発行など、運営に必要な様々な操作を行えます。

---

**コーディング初心者・開発に初めて参加する方へ**

このプロジェクトへようこそ！このセクションでは、開発を始めるにあたって知っておくと役立つ情報や、このドキュメントの読み進め方について簡単に説明します。

*   **まず何から見ればいい？**:
    *   **`7. 実行・起動方法`**: まずはご自身のパソコンでこのシステムを動かしてみましょう。ここに書かれた手順に従えば、開発用のサーバーを起動できます。特に「データベースのセットアップ」は重要です。
    *   **`4. プロジェクト構造`**: どんなファイルがどこにあるのか、大まかな地図です。特に `manager/models.py` (データ設計図) と `manager/views.py` (主な処理) がシステムの中心です。
    *   **`1. システム概要`** (このすぐ下) と **`2. 主要機能一覧`**: このシステムが何をするものなのか、どんな機能があるのかを把握できます。
*   **よく出てくる言葉（超入門）**:
    *   **Django (ジャンゴ)**: このシステムを作るために使われている、Python言語の「フレームワーク（開発を楽にするための骨組みや道具セット）」です。
    *   **モデル (`models.py`)**: システムで扱うデータ（出し物の情報、ユーザー情報など）の形や種類を決める設計図のようなものです。データベースのテーブル構造と対応します。
    *   **ビュー (`views.py`)**: ユーザーからのリクエスト（例: 「このページが見たい！」）に応じて、モデルからデータを取ってきたり、計算したりして、結果をHTMLテンプレートに渡す処理を書く場所です。
    *   **テンプレート (`templates/`フォルダ内のHTMLファイル)**: 実際にブラウザに表示される見た目を作るファイルです。ビューから渡されたデータを埋め込んで表示します。
    *   **データベース (DB)**: 様々な情報を保存しておく場所です。このプロジェクトではSQLiteという手軽なデータベースを使っています。
    *   **マイグレーション (`migrations/`フォルダ、`manage.py migrate`コマンド)**: モデル（データベース設計図）に変更があった場合、実際のデータベースにその変更を安全に適用するための仕組み・手順です。「7. 実行・起動方法」で詳しく説明します。
*   **大切なこと**:
    *   分からないことがあれば、遠慮なく他のメンバーに質問しましょう！
    *   少しずつコードを読んで、動かしてみて、慣れていくことが大切です。

---

#### 1. システム概要

本システムは、Djangoフレームワークを用いて開発されたWebアプリケーションです。文化祭の各出し物の混雑状況をリアルタイムで管理・表示し、来場者、出展者、運営者の三者にとって価値のある機能を提供することを目的とします。

#### 2. 主要機能一覧

*   **混雑状況管理**: QRコードによる入退室記録で、各出し物の現在人数をリアルタイムに把握・表示します。さらに、演劇系の出し物については、設定された公演スケジュールに基づき、現在の状態（例: 「準備中」「開演まであと10分」「上演中」「終演」など）を動的に表示する機能を持ちます。
*   **出し物情報管理**: 管理サイトから、出し物の基本情報（名称, 団体名, 紹介文, 動画, タグ, 場所等）のCRUD（作成, 読取, 更新, 削除）が行えます。特に演劇系の出し物については、複数の公演時間（開始日時・終了日時）を登録・管理することが可能です。
*   **ガチャチケット機能**: 異なる種類の出し物を5つ体験し終えたユーザーにガチャチケットを発行し、職員がQRコードでチケットの有効性を確認・使用済みにする機能です。（同じ出し物への複数回の訪問は、チケット発行条件としては1カウントとなります）
*   **ユーザー行動履歴の活用**: 来場者が各出し物に入室・退室した時刻を個別に記録し、それぞれの滞在時間を自動で算出します。これにより、より詳細なデータ分析（例: 平均滞在時間、リピート率など）や、将来的な不正利用検知機能の実現に向けた基礎データを蓄積します。
*   **評価・ランキング機能**: 来場者による「いいね」評価と、それに基づいたランキングの表示。
*   **多階層なユーザー権限**: 「来場者」「管理者」「ガチャ職員」「出し物職員」「サイネージ」の5つの役割に応じた機能制限。
*   **サイネージ表示**: 大型ディスプレイ向けに最適化された、自動更新の混雑状況表示。
*   **動画配信**: アップロードされた動画をHLS形式に自動変換し、ダウンロードを困難にするストリーミング配信。

#### 3. 技術スタック・開発環境

*   **フレームワーク**: Django
*   **言語**: Python
*   **データベース**: SQLite (開発用・デフォルト)
*   **フロントエンド**: HTML, CSS, JavaScript (外部ライブラリは限定的に使用)
*   **動画処理**: FFmpeg (別途インストールが必要)
*   **Pythonライブラリ**:
    *   `django`: Webフレームワーク本体です。
    *   `Pillow`: 画像の処理（例: アップロードされた画像の形式検証など）のためにDjangoが内部的に利用することがあるライブラリです。
    *   `ffmpeg-python`: 動画のHLS形式への変換に使用します。
    *   *(その他、Djangoフレームワーク自体や、その動作に必要な基本的なライブラリが含まれています)*
    *   *補足:* 以前のバージョンでは `qrcode` ライブラリがQRコード生成のためにリストされていましたが、現在はQRコードの表示に外部のWeb API (`https://api.qrserver.com/`) を利用しているため、このライブラリはプロジェクトから削除されました。

#### 4. プロジェクト構造

```
bunkasai_prj/
├── bunkasai_prj/       # プロジェクト設定ディレクトリ
│   ├── settings.py     # 全体の設定ファイル (DB, ALLOWED_HOSTSなど)
│   └── urls.py         # 全体のURL設定
├── manager/            # メインのアプリケーションディレクトリ
│   ├── admin.py        # 管理サイト(Django Admin)のカスタマイズ
│   ├── forms.py        # ログイン・新規登録フォームの定義
│   ├── models.py       # ★データベースの設計図 (最重要)
│   ├── views.py        # ★アプリケーションの主要ロジック (最重要)
│   ├── urls.py         # managerアプリ内のURL設定
│   ├── utils.py        # ★ビューなどで使われる補助的な便利関数 (例: 演劇状態の判定)
│   └── migrations/     # DB構造の変更履歴
├── media/              # (自動生成) ユーザーがアップロードしたファイル (動画など)
│   └── videos/
├── static/             # 主にPWA用のアイコンファイル (static/images/) を格納。CSS/JSは多くがテンプレート内記述またはCDN利用。
├── templates/          # HTMLテンプレート
│   ├── admin/
│   │   ├── base_site.html  # 管理サイトのヘッダーカスタマイズ
│   │   └── ranking.html    # ランキングページ
│   └── manager/
│       ├── base.html       # 全ページの基礎となるテンプレート
│       ├── attraction_list.html # 混雑状況一覧ページ
│       └── ... (その他各ページのHTML)
├── db.sqlite3          # データベースファイル
└── manage.py           # プロジェクト管理用スクリプト
```

#### 5. データベース設計 (`manager/models.py`)

本システムの中心となるデータ構造です。各モデルの主要なフィールドについて説明します。

*   **`Tag`**: 出し物を分類するためのタグ (例: 食べ物, 演劇)。
    *   `name` (`CharField(max_length=50)`): タグの名前（最大50文字、必須、重複不可）。
    *   `icon` (`CharField(max_length=50)`): タグに表示するRemix Iconの名前（最大50文字、任意）。
*   **`User`**: Django標準のユーザーモデル (`AbstractUser`) を拡張し、システム固有の役割や関連情報を追加。
    *   `role` (`CharField`): ユーザーの役割（例: `visitor` (来場者), `admin` (管理者), `staff` (出し物職員)など）。選択肢は `ROLE_CHOICES` で定義。
    *   `managed_attractions` (`ManyToManyField` to `Attraction`): ユーザーが「出し物職員」の場合に、担当する出し物との関連付け（複数担当可）。
*   **`Attraction`**: 文化祭の各出し物の詳細情報を格納。
    *   `group_name` (`CharField`): 出し物を運営する団体名（最大100文字）。
    *   `attraction_name` (`CharField`): 出し物の名前（最大100文字）。
    *   `description` (`TextField`): 出し物の紹介文（複数行入力可、任意入力）。
    *   `video_file` (`FileField`): 紹介動画ファイル (MP4など)。アップロードされるとHLS形式に自動変換。
    *   `hls_playlist` (`CharField(max_length=255)`): 自動生成されたHLS再生リストのパス（任意）。
    *   `tags` (`ManyToManyField` to `Tag`): この出し物に関連付けられたタグ（複数選択可）。
    *   `capacity` (`PositiveIntegerField`): 出し物の収容人数（0以上の整数）。
    *   `current_visitors` (`PositiveIntegerField`): 現在の人数（並んでいる人を含む、0以上の整数、デフォルト0）。
    *   `total_visitors` (`PositiveIntegerField`): これまでの累計来場者数（0以上の整数、デフォルト0）。
    *   `is_theater` (`BooleanField`): 演劇系の出し物かどうかを示すフラグ（はい/いいえ、デフォルト: いいえ）。
    *   `status` (`CharField`): 出し物の現在の物理的な状態（例: `available` (空き), `closed` (閉店)など）。選択肢は `STATUS_CHOICES` で定義。演劇系の場合は、`Showtime` モデルと連動して表示上の状態が変化します。
    *   `likes_count` (`PositiveIntegerField`): この出し物が獲得した「いいね」の数（0以上の整数、デフォルト0）。
    *   `entry_qr_id`, `exit_qr_id` (`UUIDField`): 入退室管理用のQRコードに対応するユニークなID。自動生成され編集不可。
    *   以前は `start_time`（開演時間）と `end_time`（閉演時間）フィールドがありましたが、これらは削除され、演劇などの公演時間は新設の `Showtime` モデルで管理されるようになりました。動画ファイルが更新されると、`save()`メソッド内でHLS変換が自動実行されます。
*   **`Showtime`**: 演劇など、特定の時間に開催されるイベントの公演スケジュールを管理します。各 `Attraction` に複数の公演時間（開始日時・終了日時）を紐付けることができます。
    *   `attraction` (`ForeignKey` to `Attraction`): 関連する出し物。（`Attraction`の情報を参照）
    *   `start_datetime` (`DateTimeField`): 公演の開始日時を保存します（日付と時刻の情報）。
    *   `end_datetime` (`DateTimeField`): 公演の終了日時を保存します（日付と時刻の情報）。
*   **`Like`**: 来場者がどの出し物に「いいね」評価をしたかの記録。
    *   `user` (`ForeignKey` to `User`): 「いいね」したユーザー。
    *   `attraction` (`ForeignKey` to `Attraction`): 「いいね」された出し物。
    *   `created_at` (`DateTimeField`): 評価が行われた日時（自動記録）。
*   **`GachaTicket`**: ガチャ抽選に参加するためのチケット情報。
    *   `user` (`ForeignKey` to `User`): チケットを所有するユーザー。
    *   `is_used` (`BooleanField`): チケットが既に使用されたかどうか（はい/いいえ、デフォルト: いいえ）。
    *   `issued_at` (`DateTimeField`): チケットの発行日時（自動記録）。
    *   `used_at` (`DateTimeField`): チケットの使用日時（任意）。
    *   `used_by` (`ForeignKey` to `User`): チケットの使用を処理した職員（任意）。
*   **`UserActivity`**: ユーザーが各出し物に入室・退室した際の詳細な記録です。同じ出し物への複数回の訪問も、それぞれ別の記録として保存されるようになりました。これらの情報は、不正対策の基礎データとなるほか、人気度分析などにも活用できます。
    *   `user` (`ForeignKey` to `User`): どのユーザーの行動かを示します。
    *   `attraction` (`ForeignKey` to `Attraction`): どの出し物に対する行動かを示します。
    *   `entry_time` (`DateTimeField`): 出し物に入室した日時が自動で記録されます。
    *   `exit_time` (`DateTimeField`): 出し物から退室した日時が記録されます（退室するまでは空の状態です）。
    *   `duration_seconds` (`PositiveIntegerField`): 滞在時間（秒単位、0以上の整数）。退室時に自動計算・保存（任意入力）。
*   **`SystemLog`**: システム内の重要な操作（例: ユーザー登録、入退室、チケット発行・使用など）を記録するログ。
    *   `timestamp` (`DateTimeField`): ログが記録された日時（自動記録）。
    *   `user` (`ForeignKey` to `User`): 操作を行ったユーザー（任意、システムによる自動操作の場合は空）。
    *   `action` (`CharField(max_length=255)`): 操作の種類を示す短い説明（最大255文字）。
    *   `details` (`TextField`): 操作に関する詳細情報（複数行入力可、任意）。

#### 6. 主要ロジック・フロー (`manager/views.py`, `manager/utils.py`)

*   **演劇状態の判定と表示**:
    *   演劇フラグ (`is_theater`) が設定された出し物の状態は、従来の人数ベースの混雑状況とは独立して、設定された複数の公演時間（`Showtime`モデル）に基づいて動的に決定されます。
    *   この状態判定のため、`manager/utils.py` ファイル内に `get_theatrical_status(attraction, current_time)` という補助関数が実装されています。この関数は、与えられた出し物インスタンスと現在時刻を基に、現在の演劇特有の状態（例: 「準備中」「開演まであとX分」「上演中」「終演」など）と、関連情報（例: 開演までの残り時間）を辞書形式で返します。
    *   `attraction_list` (出し物一覧ページビュー) や `attraction_detail` (出し物詳細ページビュー) では、この `get_theatrical_status` 関数を利用して演劇の状態を取得し、その情報をHTMLテンプレートに渡すことで、ユーザーに表示しています。
    *   サイネージ用のAPI (`attraction_api`) も、この関数から得られる情報を基に演劇の状態を提供します。
*   **入退室処理 (`process_entry`, `process_exit`)**:
    1.  QRコードのURLから`Attraction`を特定。
    2.  人数を増減させ、混雑状況を更新 (`update_attraction_status`)。
    3.  **`UserActivity`レコードの作成・更新**: 入室時には、ユーザーと出し物に紐づく新しい`UserActivity`レコードが作成され、入室時刻が記録されます。退室時には、該当する最新の未退室`UserActivity`レコードに退室時刻が記録され、同時にその訪問の滞在時間 (`duration_seconds`) がモデル内で自動計算・保存されます。（同じ出し物への複数回の訪問も、それぞれ個別の訪問記録として扱われます。）
    4.  退室時に、ガチャチケットの発行条件をチェックします。現在の条件は「異なる種類の出し物を5つ以上体験し終えていること（つまり、ユニークな5つの出し物それぞれについて、入室と退室の記録が完了していること）」です。
    また、`process_entry`（入室処理）においては、対象の出し物が演劇系の場合、`get_theatrical_status`関数によって判定された現在の演劇状態（例: 「上演中」や「終演」など、入室に適さない状態）によっては、入室を制限するチェックが追加されています。
*   **動画処理 (`Attraction`モデルの`save`メソッド)**:
    1.  動画ファイルがアップロード/変更されると`save()`が呼ばれる。
    2.  古いファイルが存在すれば、それをサーバーから物理的に削除。
    3.  `ffmpeg-python`ライブラリを通じて`FFmpeg`コマンドを呼び出し、新しい動画をHLS形式に変換。
    4.  生成された再生リストのパスを`hls_playlist`フィールドに保存。
*   **権限管理**:
    *   各View関数の冒頭で`@login_required`デコレータや`if request.user.role == ...`といった条件分岐を用いて、アクセス制御を行っている。

#### 7. 実行・起動方法

1.  **必要なツール**: Python (バージョン3.x推奨), FFmpeg がお使いのコンピュータにインストールされている必要があります。
    *   FFmpegは動画処理（HLS変換）のために必要です。インストール方法はOSによって異なりますので、別途調べて導入してください。

2.  **プロジェクトの準備**:
    *   このプロジェクトのコード一式をGitなどから取得します。
    *   コマンドライン（ターミナルやコマンドプロンプト）で、取得したプロジェクトのルートディレクトリ（この`README.md`ファイルがある場所）に移動します。

3.  **必要なPythonライブラリのインストール**:
    *   プロジェクトが必要とするPythonライブラリ（Djangoフレームワークなど）を一括でインストールします。以下のコマンドを実行してください。
        ```bash
        pip install -r requirements.txt
        ```
    *   *(補足: `requirements.txt` は、プロジェクトが依存するライブラリとそのバージョンをリストしたファイルです。)*
    *   *(もしPythonの仮想環境 (venvなど) を使う場合は、先に仮想環境を作成し、有効化してからこのコマンドを実行すると、プロジェクトごとにライブラリを分離できて便利です。)*

4.  **データベースのセットアップと更新 (マイグレーション)**:
    *   **とても重要:** このシステムは、出し物の情報やユーザー情報などをデータベースに保存します。データベースの構造（テーブルやカラムの設計）は `manager/models.py` ファイルで定義されています。
    *   この `models.py` の内容（つまりデータベースの設計図）に変更があった場合（特に新しい機能を追加したり、既存の機能を変更したりした時）、その変更を実際のデータベースに反映させる作業が必要です。この作業を「**マイグレーション (migration)**」と呼びます。
    *   マイグレーションは、基本的に以下の2つのコマンドを順に実行します。

    1.  **マイグレーションファイルの作成**:
        *   まず、Djangoにモデルの変更点を検知させ、データベースをどのように変更するかの指示書（マイグレーションファイル）を作成させます。以下のコマンドを実行します。
            ```bash
            python manage.py makemigrations manager
            ```
        *   （`manager` は、このプロジェクトの主要なアプリケーション名です。通常、モデルの変更はこの `manager` アプリ内で行われます。）
        *   このコマンドを実行すると、`manager/migrations/` ディレクトリ内に新しいマイグレーションファイル（例: `000X_xxxx.py`）が作成されることがあります（変更がなければ何も作成されません）。

    2.  **データベースへの変更適用**:
        *   次に、作成されたマイグレーションファイル（または未適用の既存マイグレーションファイル）に基づいて、実際のデータベースの構造を変更（テーブル作成やカラム追加など）します。以下のコマンドを実行します。
            ```bash
            python manage.py migrate
            ```
        *   このコマンドで、データベースが最新の状態に更新されます。

    *   **いつ実行するの？**:
        *   プロジェクトを初めてセットアップして、データベースをまっさらな状態から作成する時。
        *   Gitなどで他の人が行った変更（特にモデルの変更）を取り込んだ時。
        *   自分自身がモデルに変更を加えた後。
        *   もし「`no such table`」のようなエラーが出たら、まずマイグレーションが正しく行われているか確認しましょう。

5.  **管理者アカウントの作成**:
    *   システムの管理機能（出し物登録、ユーザー管理など）を利用するために、管理者権限を持つスーパーユーザーアカウントを作成します。以下のコマンドを実行し、指示に従ってユーザー名、メールアドレス、パスワードを設定してください。
        ```bash
        python manage.py createsuperuser
        ```

6.  **開発サーバーの起動**:
    *   ここまでの設定が完了したら、開発用のWebサーバーを起動してシステムにアクセスできます。
    *   **ローカル環境で自分だけでテストする場合**:
        ```bash
        python manage.py runserver
        ```
        起動後、ブラウザで `http://127.0.0.1:8000/` または `http://localhost:8000/` にアクセスしてください。
    *   **同じネットワーク内の他のPCやスマートフォンからもアクセス可能にする場合 (例: 実機テスト)**:
        ```bash
        python manage.py runserver 0.0.0.0:8000
        ```
        この場合、`bunkasai_prj/settings.py` ファイル内の `ALLOWED_HOSTS` リストに、サーバーを起動しているPCのIPアドレスを追加する必要があります（例: `ALLOWED_HOSTS = ['192.168.1.10']`）。PCのIPアドレスは、お使いのOSのネットワーク設定で確認できます。

7.  **システムの停止**:
    *   開発サーバーを停止するには、サーバーを起動したコマンドラインで `Ctrl+C` (Windowsの場合は `Ctrl+Break` のこともあり) を押します。

#### 8. 今後の改修・拡張案（TODOリスト）

*   **マップ機能の実装**: Figmaで作成されたデザインに基づき、静的な会場図画像上に各出し物エリアをインタラクティブに表示し、混雑状況や詳細情報と連携させる機能の実装を予定しています。（最優先課題）
*   **演劇の表示と状態管理の高度化**: 演劇系出し物の状態は、設定された複数の公演時間（`Showtime`モデル）と現在時刻に基づいて、アクセス時に動的に判定・表示されるように改善されました。今後の拡張として、より高度な状態管理（例: 公演開始/終了をトリガーとしたプッシュ通知、バックグラウンドでの定期的な状態更新による大規模イベント時のパフォーマンス最適化など）のために、CeleryやAPSchedulerといった非同期タスクキューの導入を検討できます。
*   **不正対策機能の実装**: `UserActivity`の各訪問ごとの正確な滞在時間データが記録されるようになったため、これを利用して極端に短い/長い滞在などの外れ値を検出し、ガチャチケットの不正利用などを防ぐための警告表示ロジックを`gacha_scan_view`等に実装することを検討します。
*   **フィルタ機能の強化**: タグだけでなく、「空いている順」「人気（いいね）順」でのソート機能を追加。
*   **PWAの再挑戦**: 環境起因の問題を解決し、オフライン対応やホーム画面設置機能を実装。
*   **本番環境へのデプロイ**: 開発用サーバーではなく、GunicornやNginxなどを使った、より堅牢な本番環境を構築。
