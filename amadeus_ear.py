from faster_whisper import WhisperModel
from datetime import datetime
import pyaudio
import wave
import sys
import time
import keyboard
import numpy as np
import logging

logger = logging.getLogger("AmadeusEar")

# VAD関連の設定
FORMAT        = pyaudio.paInt16 # Silero VADはint16を要求
SAMPLE_RATE   = 16000           # WhisperとSileroVADの必須要件
FRAME_SIZE    = 512             # 16kHzでの512サンプルは約32ミリ秒
CHANNELS      = 1               # モノラル

WAV_FILE = "./output.wav"


def look_for_audio_input():
    """
    デバイス上でのオーディオ系の機器情報を表示する
    """
    pa = pyaudio.PyAudio()
    for i in range(pa.get_device_count()):
        print(pa.get_device_info_by_index(i))
        print()
    pa.terminate()

class AmadeusEar:
    def __init__(self):
        logger.info("初期化中... モデルをロードしています...")
        # Whisperモデル定義
        self.model = WhisperModel(model_size_or_path="base", device="cpu", compute_type="int8")
        
        # Silero VADモデルのロード
        import torch
        self.vad_model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False,
            trust_repo=True
        )
        self.vad_iterator = utils[3](<
            self.vad_model, # utils[3] is VADIterator
            threshold=0.5, #声と判定する確率の閾値(def:0.5)
            min_speech_duration_ms=250, #これより短い音は「咳払い」などのノイズとみなして無視する（def:250ms）
            min_silence_duration_ms=1000, #★重要★ どれくらい無音が続いたら「話し終わった(end)」と判定するか（def:100ms)
            sampling_rate=SAMPLE_RATE # 16000
            )
        
        # PyAudioのインスタンス化 (常時監視用)
        self.audio = pyaudio.PyAudio()
        logger.info("初期化完了。")

    def listen(self, audio_data):
        # audio_data: 1次元のnumpy.ndarray (float32) を想定
        segments, info = self.model.transcribe(audio_data, beam_size=5, language="ja")
        #beam size:AIが次の単語を予測する際の「探索の幅」。
        logger.info("Detected language '%s' with probability %f" % (info.language, info.language_probability))
           
        # セグメント（断片）からテキストだけを抽出して、1つの文字列に結合する
        full_text = "".join([segment.text for segment in segments])
        # 結合した文字列を、関数の外（呼び出し元）に返す！
        logger.info(f"ユーザーの入力：{full_text}")
        return full_text

    def listen_autonomously(self):
        """
        VADによる常時監視ループ。
        声が聞こえたら録音を開始し、話し終わったらWhisperで推論してテキストを返す。
        Ctrlキーが押された場合は録音をブレイクしてテキスト手動入力を促す。
        """
        import torch
        logger.info("🎧 マイク監視中... (声をかけるか、Ctrlキーでテキスト入力)")
        
        stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=SAMPLE_RATE, input=True, frames_per_buffer=FRAME_SIZE)
        self.vad_iterator.reset_states() # VADの内部状態をリセット
        
        frames = []
        is_recording = False
        
        try:
            while True:
                # 1. Ctrlキーが押されたら強制的にテキスト入力モードへ移行（フォールバック）
                if keyboard.is_pressed("ctrl"):
                    print("\n[システム] 手動入力モードに切り替えました。")
                    user_input = input("[あなた]: ")
                    return user_input

                # 2. マイクから波形データを拾う
                data = stream.read(FRAME_SIZE, exception_on_overflow=False)
                
                # 3. SileroVAD用のTensorに変換
                audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                tensor_data = torch.from_numpy(audio_data)
                
                # 4. VADで声の判定
                speech_dict = self.vad_iterator(tensor_data, return_seconds=True)
                
                if speech_dict:
                    if 'start' in speech_dict:
                        is_recording = True
                        logger.info("🟢 録音開始...")
                        frames = [] # 前回のカスが残らないように確実に初期化
                    elif 'end' in speech_dict:
                        if is_recording:
                            is_recording = False
                            logger.info("🔴 録音終了。推論中...")
                            break # whileループを抜けて推論フェーズへ
                
                # 5. 録音フラグが立っている間、チャンクを保存し続ける
                if is_recording:
                    frames.append(data)
                    
        finally:
            # whileループを抜けたらストリームを安全に閉じる
            stream.stop_stream()
            stream.close()

        # ループを抜けた後、録音データ(frames)があればWhisperへ投げる
        if frames:
            raw_audio_bytes = b"".join(frames)
            
            # FORMATがint16なので、一旦int16で読んでからfloat32へキャストする（Whisper要件）
            audio_np_int = np.frombuffer(raw_audio_bytes, dtype=np.int16)
            # -1.0 〜 1.0 に正規化
            audio_float32 = audio_np_int.astype(np.float32) / 32768.0
            
            result_text = self.listen(audio_float32)
            return result_text
        else:
            return None



if __name__ == "__main__":
    # 1. まずは耳（インスタンス）を作る
    ear = AmadeusEar()

    # 2. テスト用の音声ファイルのパスを指定する
    test_audio = "test_audio.wav"

    # 3. 耳に音声を聞かせて、返ってきた結果を変数（result）に受け取る！
    print("音声を聞き取ってます...")
    reslut = ear.listen_autonomously()

    # 4. 文字起こしの確実な完了結果を画面に表示！
    if reslut:
        print("\n 【耳が脳に送ったテキスト】:")
        print(reslut)





