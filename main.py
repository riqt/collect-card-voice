#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WikiWikiからカード情報とボイスデータを取得するメインスクリプト
"""

import sys
from pathlib import Path
from urllib.parse import quote

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fetch_card_text import CardFetcher, save_to_csv
from fetch_voice_data import extract_voice_data
import pandas as pd
import time


def main():
    """
    メイン処理:
    1. WikiWikiからカード一覧を取得
    2. 各カードのボイスデータを抽出
    3. 結果をCSVに保存
    """
    # メンバー名とURLを設定
    member_name = "桂城泉"
    # メンバー名からURLを生成
    base_url = "https://wikiwiki.jp/llll_wiki/%E8%93%AE%E3%83%8E%E7%A9%BA%E5%A5%B3%E5%AD%A6%E9%99%A2"
    member_url = f"{base_url}/{quote(member_name)}"

    # 出力パス
    card_list_path = f"data/card_link_{member_name}.csv"
    output_path = f"data/card_link_with_voices_{member_name}.csv"

    print("=" * 80)
    print(f"カード情報とボイスデータの取得を開始: {member_name}")
    print("=" * 80)

    # ステップ1: カード一覧を取得
    print("\n[ステップ1] カード一覧を取得中...")
    fetcher = CardFetcher(member_url)
    cards = fetcher.fetch_cards()

    if not cards:
        print("カードデータを取得できませんでした")
        return

    # カードリストをCSVに保存
    print(f"\nカードリストをCSVに保存: {card_list_path}")
    save_to_csv(cards, card_list_path, member_name)

    # ステップ2: CSVを読み込んでボイスデータを抽出
    print("\n[ステップ2] ボイスデータを抽出中...")
    print(f"CSVから読み込み: {card_list_path}")
    df = pd.read_csv(card_list_path)

    # 新しいカラムを初期化
    df['入手時'] = ''
    df['特訓時'] = ''
    df['特訓1回目'] = ''
    df['特訓2回目'] = ''
    df['ライブ開始'] = ''
    df['スキル発動'] = ''
    df['スキル発動(クロスボイス)'] = ''
    df['SP発動'] = ''

    # 各カードのボイスデータを抽出
    total = len(df)
    for index, row in df.iterrows():
        print(f"\n進行状況: {index + 1}/{total}")
        url = row['リンク']
        voice_data = extract_voice_data(url)

        # データを更新
        for key, value in voice_data.items():
            df.at[index, key] = value

        # サーバーに負荷をかけないよう待機
        time.sleep(1)

    # ステップ3: 結果を保存
    print(f"\n[ステップ3] 結果を保存中...")
    print(f"出力先: {output_path}")
    df.to_csv(output_path, index=False, encoding='utf-8-sig')

    print("\n" + "=" * 80)
    print("完了！")
    print("=" * 80)
    print(f"取得したカード数: {total}")
    print(f"出力ファイル: {output_path}")


if __name__ == "__main__":
    main()
