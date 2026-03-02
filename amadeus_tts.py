import os
import requests
import json
from playsound import playsound
import time
import winsound

class AmadeusMouth:
    def __init__(self, host="127.0.0.1", port=50021):
        # VOICEVOXが立ち上がっているローカルの住所とポート
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        
        # 声の主（ずんだもん3 めたん2)
        self.speaker_id = 2 
        
        self.output_wav = "./tts_output.wav"

    def check_connection(self):
        """VOICEVOXアプリが起動しているか確認する初期チェック"""
        try:
            res = requests.get(f"{self.base_url}/version", timeout=2)
            print(f"VOICEVOX接続成功（Ver {res.text}）: エンジン起動確認ヨシ！")
            return True
        except requests.exceptions.RequestException:
            print(f"エラー: VOICEVOXアプリが見つかりません。起動してからやり直してください。({self.base_url})")
            return False

    def speak(self, text):
        """テキストをVOICEVOXに投げて、生成された音声を再生するメソッド"""
        #print(f"\n[Mouth] {text} （←これを音声化します）")

        # ----------------------------------------------------
        # 1. 音声合成用の「設計図（Query）」をVOICEVOXに作ってもらう
        # ----------------------------------------------------
        query_payload = {'text': text, 'speaker': self.speaker_id}
        try:
            query_response = requests.post(
                f"{self.base_url}/audio_query", 
                params=query_payload
            )
            
            if query_response.status_code != 200:
                print("エラー: 設計図(audio_query)の作成に失敗したわ。")
                return

            # ----------------------------------------------------
            # 2. 設計図を元に、「WAVファイル（音声データ）」を合成してもらう
            # ----------------------------------------------------
            synthesis_payload = {'speaker': self.speaker_id}
            audio_response = requests.post(
                f"{self.base_url}/synthesis",
                params=synthesis_payload,
                json=query_response.json() # さっき1で作った設計図を渡す
            )

            if audio_response.status_code != 200:
                print("エラー: 音声データの合成(synthesis)に失敗したわ。")
                return
                
        except requests.exceptions.RequestException as e:
            # VOICEVOXが立ち上がっていない時にシステムクラッシュするのを防ぐ
            print(f"\n[Mouth] エラー: VOICEVOXに接続できません。アプリが起動しているか確認してね。（{e}）")
            return

        # ----------------------------------------------------
        # 3. 生成されたWAVデータ（バイナリ）を一時ファイルに保存する
        # （※毎回違う名前を作成：time.time()でミリ秒を取る）
        # ----------------------------------------------------
        temp_filename = f"./tts_temp_{int(time.time() * 1000)}.wav"
        
        with open(temp_filename, "wb") as f:
            f.write(audio_response.content)
        # ----------------------------------------------------
        # 4. 再生する（Windows標準の winsound を使用）
        # ----------------------------------------------------
        #print("音声の再生を開始します……")
        import subprocess
        # PowerShellの再生コマンドを直接叩く
        command = f'powershell -c (New-Object Media.SoundPlayer "{temp_filename}").PlaySync()'
        subprocess.run(command, shell=True)
        
        # ----------------------------------------------------
        # 5. 再生が終わったら、ゴミを残さないようにファイルを削去（クリーンアップ）
        # ----------------------------------------------------
        try:
            os.remove(temp_filename)
        except Exception as e:
            # 万が一ロックされて消せなかった時用（次回の名前が違うからプログラムは止まらない)
            pass

# テスト実行用のブロック
if __name__ == "__main__":
    # テストする時は、必ず裏でVOICEVOXアプリを起動しておくこと！
    mouth = AmadeusMouth()
    
    # 接続確認
    if mouth.check_connection():
        # テスト発話
        mouth.speak("初めまして。私のアマデウスシステムへようこそ。私は牧瀬クリスです。")
