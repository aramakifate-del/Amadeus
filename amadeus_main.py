from amadeus_core import AmadeusBrain
from amadeus_ear import AmadeusEar
import os
import sys
import keyboard
import time


def main():
    print("システム起動中...各モジュールを初期化します...")

    #ここで各器官のインスタンスを作成
    brain = AmadeusBrain()
    ear = AmadeusEar()
   
    print("\n初期化完了。Amadeus System 起動。")
    print("終了するには Ctrl+C を押してください。")
    print("スペースキーを押すと、10秒録音開始、またはctrlキーを押すと、テキスト入力開始です。")

    #対話ループの処理を書く
    while True:
        try:
            user_input = None #まず入力を受け取る（フラグ管理、変数初期化）
            
            #スペースキーで録音開始の処理
            if keyboard.is_pressed("space"):
                print("録音開始")
                user_input = ear.VoiceTyper()
                print(user_input)
            
            #ctrlならチャットモード
            elif keyboard.is_pressed("ctrl"): #enterだとinput時に2回反応してしまうのでctrlに変更。だるすぎ！！
                print("テキスト入力開始")
                user_input = input("\n[あなた]") #ユーザーの入力

            # user_input変数が代入されてるなら....
            if user_input:
                #LLMの関数呼び出し、聞き取ったテキスト（user_text）を、脳（brain）に渡して考えさせる
                print("\n[Amadeus]: ", end="")
                #yieldだるすぎ！！ gen関数は関数定義でforで回した上で、呼び出しでもforで回さないと動かない！！
                for chunk in brain.ask_stream(user_input): #streamとyieldの非同期処理により、リアルタイム性を重視して思考を生成
                    print(chunk, end="", flush=True)  # ← 受け取った文字をここで画面に出力（改行なしで繋げる）
                print("\n") # ← 最後に1回だけ綺麗に改行する
                print("スペースキーを押すと、10秒録音開始、またはEnterキーを押すと、テキスト入力開始です。")
                time.sleep(1) #CPU負荷を抑えるために少し待つ
        
            #Ctrl+C が押されたら、無限ループを安全に破壊して終了する
        except KeyboardInterrupt:
            print("\nシステムをシャットダウンします。おやすみなさい。")
            sys.exit(0)

# このファイルが直接実行された時だけ、main() を呼び出すおまじない
if __name__ == "__main__":
    main()





