from faster_whisper import WhisperModel
from datetime import datetime
import pyaudio
import wave
import sys
import time
import keyboard

FORMAT        = pyaudio.paInt16
TIME          = 10           # 録音時間[s]
SAMPLE_RATE   = 44100        # サンプリングレート
FRAME_SIZE    = 1024         # フレームサイズ
CHANNELS      = 1            # モノラルかバイラルか
INPUT_DEVICE_INDEX = 0       # マイクのチャンネル
NUM_OF_LOOP   = int(SAMPLE_RATE / FRAME_SIZE * TIME)

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
        #自分のモデル定義
        self.model = WhisperModel(model_size_or_path="base", device="cpu", compute_type="int8")

    def listen(self, audio_file_path):
        segments, info = self.model.transcribe(audio_file_path, beam_size=5, language="ja")
        #beam size:AIが次の単語を予測する際の「探索の幅」。
        print("Detected language '%s' with probability %f" % (info.language, info.language_probability))
           
        # セグメント（断片）からテキストだけを抽出して、1つの文字列に結合する
        full_text = "".join([segment.text for segment in segments])
        # 結合した文字列を、関数の外（呼び出し元）に返す！
        return full_text

    def VoiceTyper(self): #ここにキーの監視処理と、録音の処理を書く。

        #pyaudioをインスタンス化
        self.audio = pyaudio.PyAudio() 
       
        #録音開始
        self.stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=SAMPLE_RATE, input=True, frames_per_buffer=FRAME_SIZE)

        #録音データを格納する空箱を用意
        frames = []
       
        #録音データをNUM_OF_LOOP分繰り返して格納、録音終了。(後にこれはspaceで録音終了に変更する)
        for i in range(NUM_OF_LOOP):
            data = self.stream.read(FRAME_SIZE)
            frames.append(data) #最終的に文字起こしされたテキストをAmadeusCore(脳)に返す

        #録音データを保存
        with wave.open(WAV_FILE, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(FORMAT))
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(b"".join(frames))
        print("録音完了")

        #録音ファイルを渡して、文字起こしを実行
        result_text = self.listen(WAV_FILE)
        return result_text



if __name__ == "__main__":
    # 1. まずは耳（インスタンス）を作る
    ear = AmadeusEar()

    # 2. テスト用の音声ファイルのパスを指定する
    test_audio = "test_audio.wav"

    # 3. 耳に音声を聞かせて、返ってきた結果を変数（result）に受け取る！
    print("音声を聞き取ってます...")
    reslut = ear.VoiceTyper()

    # 4. 文字起こしの確実な完了結果を画面に表示！
    print("/n 【耳が脳に送ったテキスト】:")
    print(reslut)





