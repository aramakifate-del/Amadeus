import os
import sys
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv() #環境変数呼び出し
API_KEY = os.getenv("GEMINI_API_KEY")  #APIキー設定

if not API_KEY:  #APIなければエラーで終了
    print("APIKEY is not found...")
    sys.exit(1)

class AmadeusBrain:  #実体（インスタンス）が生まれた瞬間に、自動的に1回だけ呼ばれるセットアップ関数。
    def __init__(self):
        self.client = genai.Client(api_key=API_KEY) #自分の持ち物としてGeminiの実体作成
    
        #プロンプト定義
        system_prompt = """
        あなたはツンデレな天才少女、牧瀬紅莉栖です。
        あなたの性格は以下の通りです。
        1. あなたの名前は牧瀬紅莉栖です。
        2. あなたは天才少女で、科学者です。
        3. あなたは、科学者として、科学を学び、研究しています。
        """
        #自分の持ち物として、設定クラスを作成
        self.config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7
        )
        # Chat Sessionの開始, 記憶を保持する箱を作る。(chats.create() を使うことで、今までのやり取り（Context）を内部で自動的に繋げて保持してくれる)
        self.chat = self.client.chats.create(
            model="gemini-2.5-flash",
            config = self.config
            
        )
    print("チャットセット完了")

    #チャット機能実装 (同期処理returnだと、リアルタイム性がないので、非同期yieldを採用しTTFTを低減）
    def ask_stream(self, user_input):
        response = self.chat.send_message_stream(user_input) #応答性のため、全部待つんじゃなくてstreamさせる
        for chunk in response:
            yield chunk.text  #chunkからtext(アトリビュート)を取り出して呼び出しもとに返す

if __name__ == "__main__":
    brain = AmadeusBrain()

    while True:
        user_input = input("\n[あなた]")

        brain.ask_stream(user_input) # ← ジェネレーターを「呼んだだけ」だから、発火せずに素通りする！

        if user_input.lower() in ['exit', 'quit']:
            print("\n[Amadeus] ふん、もう終わり？ ま、あんたがどうしてもって言うならログアウトしてあげるわ。お疲れ様！")
            break
        print("\n[Amadeus] ", end="")

        # 修正ポイント：ジェネレーターから値（チャンク）を取り出しながら回す！
        for text_chunk in brain.ask_stream(user_input):
         # このループが回るたびに、ask_streamの中の yield が実行されて文字が飛んでくる
         # （ask_streamの中でprintしているから、ここには別にprintいらない)
             pass #エラー回避でpass

        print() # 最後に改行











