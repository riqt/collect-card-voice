#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSVファイル内のカードリンクを検証するスクリプト
"""

import csv
import requests
import time
from typing import List, Dict


def load_csv(csv_path: str) -> List[Dict[str, str]]:
    """
    CSVファイルを読み込む

    Args:
        csv_path: CSVファイルのパス

    Returns:
        CSVデータのリスト
    """
    data = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data


def verify_link(url: str, timeout: int = 10) -> tuple[bool, int, str]:
    """
    リンクが有効かどうかを検証

    Args:
        url: 検証するURL
        timeout: タイムアウト時間（秒）

    Returns:
        (成功フラグ, ステータスコード, エラーメッセージ)
    """
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        # HEADメソッドが失敗した場合はGETを試す
        if response.status_code >= 400:
            response = requests.get(url, timeout=timeout, allow_redirects=True)

        success = 200 <= response.status_code < 400
        return success, response.status_code, ""
    except requests.RequestException as e:
        return False, 0, str(e)


def verify_all_links(csv_path: str, delay: float = 0.5):
    """
    CSV内の全リンクを検証

    Args:
        csv_path: CSVファイルのパス
        delay: リクエスト間の待機時間（秒）
    """
    print(f"CSVファイルを読み込み中: {csv_path}")
    data = load_csv(csv_path)
    print(f"{len(data)}件のリンクを検証します\n")

    results = {
        'success': [],
        'failed': [],
        'error': []
    }

    for i, row in enumerate(data, 1):
        card_name = row.get('カード名', '')
        rarity = row.get('レアリティ', '')
        link = row.get('リンク', '')

        print(f"[{i}/{len(data)}] {rarity} {card_name}")
        print(f"  URL: {link}")

        success, status_code, error_msg = verify_link(link)

        if success:
            print(f"  ✓ 成功 (ステータス: {status_code})")
            results['success'].append(row)
        elif status_code > 0:
            print(f"  ✗ 失敗 (ステータス: {status_code})")
            results['failed'].append({**row, 'status': status_code})
        else:
            print(f"  ✗ エラー: {error_msg}")
            results['error'].append({**row, 'error': error_msg})

        # サーバーへの負荷を軽減するため待機
        if i < len(data):
            time.sleep(delay)

    # 結果のサマリーを表示
    print("\n" + "=" * 80)
    print("検証結果サマリー")
    print("=" * 80)
    print(f"成功: {len(results['success'])}件")
    print(f"失敗: {len(results['failed'])}件")
    print(f"エラー: {len(results['error'])}件")

    if results['failed']:
        print("\n失敗したリンク:")
        for item in results['failed']:
            print(f"  - {item['レアリティ']} {item['カード名']}")
            print(f"    URL: {item['リンク']}")
            print(f"    ステータス: {item['status']}")

    if results['error']:
        print("\nエラーが発生したリンク:")
        for item in results['error']:
            print(f"  - {item['レアリティ']} {item['カード名']}")
            print(f"    URL: {item['リンク']}")
            print(f"    エラー: {item['error']}")


def main():
    """メイン関数"""
    csv_path = "data/card_link.csv"
    verify_all_links(csv_path, delay=0.5)


if __name__ == "__main__":
    main()
