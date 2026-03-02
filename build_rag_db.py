import chromadb
import os

# ファイルパスの設定
cleansed_file_path = "C:\\Users\\ren\\.gemini\\antigravity\\scratch\\Python_Amadeus_Lab\\AmadeusSystem\\kurisu_corpus_cleansed.txt"
db_path = "C:\\Users\\ren\\.gemini\\antigravity\\scratch\\Python_Amadeus_Lab\\AmadeusSystem\\chroma_db"

def build_vector_db():
    print("🧠 ChromaDB（ベクトルデータベース）の構築を開始します...")

    # 1. 綺麗になったテキストデータを読み込む
    with open(cleansed_file_path, 'r', encoding='utf-8') as f:
        # 今回は1行＝1セリフ＝1チャンクとして処理する
        chunks = [line.strip() for line in f.readlines() if line.strip()]

    print(f"📦 読み込んだチャンク（セリフ）数: {len(chunks)}個")

    # 2. ChromaDBのクライアントを初期化（ローカルフォルダにDBを作成）
    client = chromadb.PersistentClient(path=db_path)

    # 3. コレクション（テーブルのようなもの）の作成。既にあれば取得
    # get_or_create を使うことで、何度実行してもエラーにならない
    collection = client.get_or_create_collection(name="kurisu_memories")

    # 4. データをChromaDBに挿入（ここで自動的にEmbedding計算が行われる）
    # ChromaDBはデフォルトで 'all-MiniLM-L6-v2' という軽量な英語/多言語モデルを使ってベクトル化する
    print("⏳ ベクトル化（Embedding）とデータベースへの保存を実行中...")
    
    # Chromaにはテキストと、それぞれの一意なIDを渡す必要がある
    ids = [f"memory_{i}" for i in range(len(chunks))]
    
    collection.add(
        documents=chunks,
        ids=ids
    )

    print(f"✅ 完了！ {len(chunks)}個の記憶がベクトル空間にマッピングされました。")
    print(f"💾 データベース保存先: {db_path}")

    # 簡単なテスト検索（Retrieval）を実行してみる
    test_query = "タイムマシンについてどう思う？"
    print(f"\n🔍 テスト検索: 「{test_query}」")
    
    results = collection.query(
        query_texts=[test_query],
        n_results=3 # Top-K（上位3件）を取得
    )
    
    for i, doc in enumerate(results['documents'][0]):
        print(f"  [{i+1}] {doc}")

if __name__ == "__main__":
    build_vector_db()
