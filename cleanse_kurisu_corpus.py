import pandas as pd
import re

print("--- [Step 1: コーパスの読み込み] ---")
# 1. 助手（ユーザー）が集めた手動の生データ
manual_corpus_path = "raw_kurisu_corpus_ver2.txt"
# 2. Geminiが生成した合成データ
synthetic_corpus_path = "raw_kurisu_synthetic_corpus.csv"

# 合成データをDataFrameとして読み込む（エラー行はスキップ）
try:
    df_synthetic = pd.read_csv(synthetic_corpus_path, on_bad_lines='skip', encoding='utf-8', names=['user_input', 'kurisu_response'])
    print(f"[SUCCESS] 合成コーパス読み込み成功: {len(df_synthetic)} 件")
except Exception as e:
    print(f"[ERROR] 読み込みエラー: {e}")
    df_synthetic = pd.DataFrame(columns=["user_input", "kurisu_response"])

# ==============================================================================
# 【Pandasによるクレンジング実装】
# ==============================================================================
print("\n--- [Step 2: データのクレンジング開始] ---")

# 1. 欠損値（NaN）の削除
df_synthetic = df_synthetic.dropna()

# 2. 表現のクリーニング（Geminiの変な口調を少し補正）
# 「だよ」「さ」などの少し違う語尾を紅莉栖っぽく置換
df_synthetic['kurisu_response'] = df_synthetic['kurisu_response'].str.replace(r'だよ', 'わよ', regex=True)
df_synthetic['kurisu_response'] = df_synthetic['kurisu_response'].str.replace(r'さ$', 'わ', regex=True)

# 3. 前後の空白文字の削除（トリミング）
df_synthetic['user_input'] = df_synthetic['user_input'].str.strip()
df_synthetic['kurisu_response'] = df_synthetic['kurisu_response'].str.strip()

# 4. 重複データの削除
df_synthetic = df_synthetic.drop_duplicates(subset=['user_input'])

print(f"[CLEAN] クレンジング後のデータ数: {len(df_synthetic)} 件")

# ==============================================================================
# 手動コーパスとの結合（今回は合成データのみをベースにするためスキップし、そのまま保存）
# ==============================================================================
output_path = "cleansed_kurisu_corpus.csv"
df_synthetic.to_csv(output_path, index=False, encoding='utf-8')

print(f"\n[DONE] クレンジング完了: 綺麗な学習用データセット '{output_path}' の生成が完了しました！")
