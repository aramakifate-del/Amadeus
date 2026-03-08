from amadeus_core import AmadeusBrain
from amadeus_ear import AmadeusEar
from amadeus_tts import AmadeusMouth
import os
import sys
import keyboard
import time

def main():
    print("システム起動中...各モジュールを初期化します...")

    #ここで各器官のインスタンスを作成
    brain = AmadeusBrain()
    ear = AmadeusEar()
    mouth = AmadeusMouth()
   
    print("\n初期化完了。Amadeus System 起動。(自律型VADモード)")
    print("終了するには Ctrl+C を押してください。")

    #対話ループの処理を書く
    while True:
        try:
            # VAD搭載の自律型Earに監視を完全に委譲する（ブロック処理）
            user_input = ear.listen_autonomously()

            # user_input変数が代入されてる（声かテキストが返ってきた）なら....
            if user_input:
                #LLMの関数呼び出し、聞き取ったテキスト（user_text）を、脳（brain）に渡して考えさせる
                print("\n[Amadeus]: ", end="")

                #chunkを一時格納する変数を用意
                stream_buffer = ""
                try:
                    #yieldだるすぎ！！ gen関数は関数定義でforで回した上で、呼び出しでもforで回さないと動かない！！
                    for chunk in brain.ask_stream(user_input): #streamとyieldの非同期処理により、リアルタイム性を重視して思考を生成
                        print(chunk, end="", flush=True)  # ← 受け取った文字をここで画面に出力（改行なしで繋げる）
                        
                        # stream_bufferにchunkを追加（ただし、VOICEVOX用に改行文字は消してあげる）
                        stream_buffer += chunk.replace("\n", "")

                        # chunkの中に「文の終わり（句点や感嘆符）」が含まれているか判別する
                        # \n で切ると文の途中で喋りだすので、\n は判定から外す！
                        if any(p in chunk for p in ["。", "！", "？", "!", "?", ".", "…"]):
                            if stream_buffer.strip(): # 空白だけの場合は飛ばす
                                # Mouthクラスのインスタンスを呼び出し、stream_bufferを渡す
                                mouth.speak(stream_buffer)
                                # stream_bufferを初期化
                                stream_buffer = ""
                    
                    # ▼▼ これが残飯処理（ループを抜けた後に残った最後のストリームを喋る） ▼▼
                    if stream_buffer.strip(): 
                        mouth.speak(stream_buffer)
                        
                except Exception as e:
                    # GeminiのAPI制限(429)等のエラーをここでキャッチしてシステムダウンを防ぐ
                    error_msg = f"\n[System Error] 脳の処理中にエラーが発生しました（API制限の可能性）: {e}"
                    print(error_msg)
                    mouth.speak("ごめんなさい、ちょっと頭が痛いわ。少し休ませてちょうだい。")
                
                print("\n") # 最後に1回だけ綺麗に改行する
                time.sleep(1) #CPU負荷を抑えるために少し待つ
        
            #Ctrl+C が押されたら、無限ループを安全に破壊して終了する
        except KeyboardInterrupt:
            print("\nシステムをシャットダウンします。おやすみなさい。")
            sys.exit(0)

# このファイルが直接実行された時だけ、main() を呼び出すおまじない
if __name__ == "__main__":
    main()





