import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
import os

print("--- [Step 1: 初期化と準備] ---")

# 1. クレンジング済みのコーパス（学習データ）を読み込む
csv_path = "cleansed_kurisu_corpus.csv"
if not os.path.exists(csv_path):
    print(f"[ERROR] {csv_path} が見つかりません。先にクレンジングを実行してください。")
    exit(1)

df = pd.read_csv(csv_path, encoding='utf-8')
print(f"✅ コーパス読み込み完了: {len(df)} 件の会話データ")

# 2. ローカルのChromaDBをセットアップ
# ※ amadeus_core.py と同じディレクトリ（./memory_db）を指定すること
db_path = "./memory_db"
print(f"📂 ChromaDBの保存先: {db_path}")

client = chromadb.PersistentClient(path=db_path)

# 3. Embedding関数の定義（完全ローカル対応、外部API不要）
# amadeus_core.py と完全に同じモデル（all-MiniLM-L6-v2）を使用する
print("🧠 Embeddingモデル (all-MiniLM-L6-v2) をロード中...")
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# 4. コレクション（テーブル）の取得または作成
# ※ amadeus_core.py が検索しにいくコレクション名は "kurisu_memories"
collection_name = "kurisu_memories"

# すでにデータが入っている場合は一旦消去して作り直す（クリーンな初期状態にするため）
try:
    client.delete_collection(name=collection_name)
    print("🗑️ 既存の kurisu_memories コレクションを削除（リセット）しました。")
except Exception as e:
    pass # そもそもコレクションが存在しない場合はスルー

# コレクションを新規作成（Embedding関数をセット）
collection = client.create_collection(
    name=collection_name, 
    embedding_function=sentence_transformer_ef
)

print("\n--- [Step 2: 記憶データのベクトル化とDB格納 (インサート)] ---")

# PandasのデータをChromaDBに書き込むためのリストを準備
documents = [] # RAGでLLMに渡す実データ（紅莉栖の返答）
metadatas = [] # 検索用のメタデータ（ユーザーの入力など）
ids = []       # 各データのユニークなID

for i, row in df.iterrows():
    # user_input（ユーザーの言葉）と kurisu_response（紅莉栖の返答）を取得
    user_input = str(row['user_input'])
    kurisu_res = str(row['kurisu_response'])
    
    # 【RAGの検索アーキテクチャ設計】
    # 検索システム（ChromaDB）は、ユーザーの入力に「近い」ベクトルを探す。
    # そのため、Embeddingされる大元のテキスト（document）に、"ユーザーの入力" を必ず含めておくことで、検索ヒット率を劇的に上げるテクニック。
    combined_text = f"ユーザーの入力: {user_input} \n紅莉栖の返答: {kurisu_res}"
    
    documents.append(combined_text)
    
    # 検索後にLLMが扱いやすいように、メタデータに分離して保持しておく
    metadatas.append({"trigger": user_input, "response": kurisu_res})
    
    # IDは一意にする（例: memory_0, memory_1...）
    str_id = f"memory_{i}"
    ids.append(str_id)

print(f"📥 {len(documents)} 件のデータをベクタライズ（数値化）して保存中...（数秒かかります）")

# ChromaDBに一括インサート（ここでEmbeddingモデルが自動的にテキストをベクトル化する）
collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)

print("\n--- [完了] ---")
print("✅ 牧瀬紅莉栖の全記憶データが ChromaDB に物理コンパイルされました！")
print("これで AmadeusCore.py から RAG として高精度な返答を引き出せるはずです！")
