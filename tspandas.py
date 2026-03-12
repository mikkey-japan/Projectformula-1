import pandas as pd
import os


# 正しいパスを設定（rをつけることでバックスラッシュをエスケープ文字として扱わなくなります）
base_path = r"f1_cache\2026\2026-03-08_Australian_Grand_Prix\2026-03-07_Qualifying"
file_path = os.path.join(base_path, "position_data
                         .ff1pkl")

# pickleファイルの読み込み
df_raw = pd.read_pickle(file_path)
print(f"データの型: {type(df_raw)}")

if isinstance(df_raw, dict):
    print(f"キー一覧: {list(df_raw.keys())}")

    # FastF1の内部データ構造（一般に 'data' キーに本体が入っています）
    if 'data' in df_raw:
        content = df_raw['data']
        print(f"Content ('data') の型: {type(content)}")

        # もし中身がDataFrameに変換可能なら変換する
        try:
            # データの形状によって最適に表示
            if isinstance(content, (list, tuple)):
                print(f"要素数: {len(content)}")
                if len(content) > 0:
                    print("最初の1要素のサンプル:")
                    print(content[0])
            else:
                print(content)
        except Exception as e:
            print(f"表示エラー: {e}")
else:
    # 既に DataFrame の場合
    print("--- データの先頭 5行 ---")
    print(df_raw.head())
    print("\n--- カラム一覧 ---")
    print(df_raw.columns)
    print("\n--- データ形状 (行数, 列数) ---")
    print(df_raw.shape)
