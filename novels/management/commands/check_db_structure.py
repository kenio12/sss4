from django.core.management.base import BaseCommand
import psycopg2
import os

class Command(BaseCommand):
    help = '旧DBの構造を確認する'

    def handle(self, *args, **kwargs):
        try:
            # OLD_DATABASE_URLを使用
            database_url = os.getenv('OLD_DATABASE_URL')
            if not database_url:
                self.stdout.write(self.style.ERROR('OLD_DATABASE_URLが設定されていません'))
                return

            self.stdout.write(f"接続先: {database_url}")  # 接続先を表示（パスワードは隠す）
            
            connection = psycopg2.connect(database_url)
            cursor = connection.cursor()

            # テーブル一覧を取得
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
            """)
            
            tables = cursor.fetchall()
            
            if not tables:
                self.stdout.write("テーブルが見つかりません")
                return

            self.stdout.write(self.style.SUCCESS("=== 旧DBのテーブル一覧 ==="))
            for table in tables:
                table_name = table[0]
                self.stdout.write(f"\nテーブル: {table_name}")
                
                # 各テーブルのカラム情報を取得
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                
                self.stdout.write("  カラム:")
                for column in cursor.fetchall():
                    nullable = "NULL可" if column[2] == 'YES' else "NOT NULL"
                    self.stdout.write(f"    - {column[0]} ({column[1]}) {nullable}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'エラーが発生しました: {str(e)}'))
            self.stdout.write(self.style.ERROR(f'接続情報: {database_url}'))  # デバッグ用
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()
