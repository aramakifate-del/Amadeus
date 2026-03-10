import os
import requests
import time
import queue
import threading
import pyaudio
import wave
import io
import logging

logger = logging.getLogger("AmadeusMouth")

class AmadeusMouth:
    def __init__(self, host="127.0.0.1", port=50021):
        # VOICEVOXが立ち上がっているローカルの住所とポート
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        
        # 声の主（ずんだもん3 めたん2)
        self.speaker_id = 2 
        
        # 【アーキテクチャ改修】非同期処理のためのキューとスレッドの準備
        self.audio_queue = queue.Queue()
        self.is_running = True # スレッドを安全に動かし続けるためのフラグ
        
        # PyAudioのインスタンスとストリーム（土管）を入れる箱
        # クラスが生まれた瞬間にPyAudio本体だけは起動しておく
        self.p = pyaudio.PyAudio()
        self.stream = None
        
        # コンシューマースレッド（裏で合成・再生を直列で回し続ける係員）を起動
        # daemon=True にすることで、メインプログラム終了時に自動で道連れになって死ぬ
        self.worker_thread = threading.Thread(target=self._play_loop, daemon=True)
        self.worker_thread.start()

    def check_connection(self):
        """VOICEVOXアプリが起動しているか確認する初期チェック"""
        try:
            res = requests.get(f"{self.base_url}/version", timeout=2)
            logger.info(f"VOICEVOX接続成功（Ver {res.text}）: エンジン起動確認ヨシ！")
            return True
        except requests.exceptions.RequestException:
            logger.error(f"VOICEVOXアプリが見つかりません。起動してからやり直してください。({self.base_url})")
            return False

    def speak(self, text):
        """
        【プロデューサー側の処理】
        テキストをキュー（箱）にただ投げ入れるだけ。
        合成も再生もここでは行わないため、一瞬（0.0001秒）でメインループへ処理を返す！
        """
        self.audio_queue.put(text)
        #print(f"[Mouth/Queue] '{text}' をキューに追加しました。（現在待機中: {self.audio_queue.qsize()} 個）")

    def _play_loop(self):
        """
        【コンシューマー側の処理】
        バックグラウンドスレッドで無限ループし、キューにテキストが入ってきたら取り出して合成・再生する。
        ここが直列（シーケンシャル）で動くため、将来GPT-SoVITS等にした際も文脈が崩壊しない。
        """
        while self.is_running:
            try:
                # キューからテキストを取り出す。何もなければ1秒だけ待機してループの先頭に戻る
                text = self.audio_queue.get(timeout=1.0)
            except queue.Empty:
                continue
                
            # ----------------------------------------------------
            # 1. 音声合成用の「設計図（Query）」をVOICEVOXに作ってもらう
            # ----------------------------------------------------
            query_payload = {'text': text, 'speaker': self.speaker_id}
            try:
                query_response = requests.post(f"{self.base_url}/audio_query", params=query_payload)
                if query_response.status_code != 200:
                    logger.error("設計図(audio_query)の作成に失敗したわ。")
                    self.audio_queue.task_done()
                    continue

                # ----------------------------------------------------
                # 2. 設計図を元に、「WAVファイル（音声データ）」を合成してもらう
                # ----------------------------------------------------
                synthesis_payload = {'speaker': self.speaker_id}
                audio_response = requests.post(
                    f"{self.base_url}/synthesis",
                    params=synthesis_payload,
                    json=query_response.json()
                )

                if audio_response.status_code != 200:
                    logger.error("音声データの合成(synthesis)に失敗したわ。")
                    self.audio_queue.task_done()
                    continue
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"VOICEVOXに接続できません。({e})")
                self.audio_queue.task_done()
                continue

            # ----------------------------------------------------
            # 3. 取得したWAVデータ（バイナリ）をメモリ上に展開して PyAudio で再生する
            # ※ ストリームの常時開放により、2回目以降のチャンクは初期化ラグ・ゼロで再生！
            # ----------------------------------------------------
            try:
                # バイナリデータをまるでファイルのように扱うための呪文 (BytesIO)
                audio_io = io.BytesIO(audio_response.content)
                
                # waveモジュールでWAVヘッダーを読み飛ばす（ヘッダー解析）
                with wave.open(audio_io, 'rb') as wf:
                    
                    # [最適化の実装] ストリームがまだ開いていなければ、初回チャンクのヘッダー情報で開通（Open）する
                    if self.stream is None:
                        #print("[System Debug] PyAudioストリームを初回設定で常時開放します")
                        self.stream = self.p.open(format=self.p.get_format_from_width(wf.getsampwidth()),
                                        channels=wf.getnchannels(),
                                        rate=wf.getframerate(),
                                        output=True)
                    
                    # チャンクごとに波形データ（Raw PCM）だけを読み込んでスピーカーに流し込む
                    chunk_size = 1024
                    data = wf.readframes(chunk_size)
                    
                    while data:
                        self.stream.write(data)
                        data = wf.readframes(chunk_size)
                        
                    # 【重要】ストリームのクローズ（stream.close）はループ内で行わない！
                    # 次のチャンクが来た時にそのままこの土管に流し込むため、開けっ放し（Keep Connection）にする。

            except Exception as e:
                logger.error(f"PyAudioでのインメモリ再生中にエラーが発生しました: {e}")
            finally:
                # タスク完了をキューに通知
                self.audio_queue.task_done()

    def wait_until_done(self):
        """キューの中身（未再生の音声）がすべて処理されるまで待機する関数（シャットダウン用）"""
        self.audio_queue.join()
        
        # 全ての処理が終わってから（プログラム終了時など）、最後のお片付けとして土管を閉じる
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

# テスト実行用のブロック
if __name__ == "__main__":
    mouth = AmadeusMouth()
    
    if mouth.check_connection():
        print("テスト1文目を投入...")
        mouth.speak("初めまして。私のアマデウスシステムへようこそ。")
        print("テスト2文目を投入...")
        mouth.speak("私は牧瀬クリスです。現在、PyAudioストリームの常時開放による超低遅延再生をテストしています。")
        
        print("\n[テスト画面] テキストの投入完了。メインスレッドは自由に動けます！")
        print("[テスト画面] 音声の再生完了を待ちます...\n")
        
        # これを呼ばないと、裏の再生スレッドが動く前にプログラムが終了（殺されて）しまう
        mouth.wait_until_done()
        print("\n全ての最適化インメモリ再生処理が完了、ストリームを安全に解放しました。")
