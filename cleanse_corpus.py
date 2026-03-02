import os
import re

# ファイルパスの設定
raw_file_path = "C:\\Users\\ren\\.gemini\\antigravity\\scratch\\Python_Amadeus_Lab\\AmadeusSystem\\raw_kurisu_corpus.txt"
clean_file_path = "C:\\Users\\ren\\.gemini\\antigravity\\scratch\\Python_Amadeus_Lab\\AmadeusSystem\\kurisu_corpus_cleansed.txt"

def cleanse_corpus(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    cleansed_lines = []
    
    for line in lines:
        # 1. 改行文字を削除
        line = line.strip()
        
        # 2. 空行をスキップ
        if not line:
            continue
            
        # 3. 「〇話」のようなエピソードヘッダーをスキップ
        if re.match(r"^\d+話$", line) or re.match(r"^[１-９]+話$", line):
            continue
            
        # 4. 「」の鉤括弧を削除（今回はセリフのみのテキストなので不要）
        line = re.sub(r"[「」]", "", line)
        
        # 5. カッコ書き（ト書きや状況説明）を非貪欲マッチで削除
        # 例: "(幽霊？) 己は警察に突き出されたいか？" -> " 己は警察に突き出されたいか？"
        line = re.sub(r"\(.*?\)", "", line)
        line = re.sub(r"（.*?）", "", line)
        
        # 6. 先頭や末尾に残った空白を再度削除
        line = line.strip()
        
        # 7. ゴミを消した結果、空になってしまった行はスキップ
        if not line:
            continue
            
        cleansed_lines.append(line)

    # 綺麗になったテキストを別ファイルに書き出す
    with open(output_path, 'w', encoding='utf-8') as f:
        for cl in cleansed_lines:
            f.write(cl + "\n")
            
    print(f"✅ クレンジング完了: {len(lines)}行 の生データから {len(cleansed_lines)}行 の純粋なセリフを抽出しました。")
    print(f"保存先: {output_path}")

if __name__ == "__main__":
    cleanse_corpus(raw_file_path, clean_file_path)
