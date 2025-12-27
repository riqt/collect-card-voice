#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WikiWikiページから藤島慈の実装カード一覧を取得するスクリプト
"""

import csv
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from urllib.parse import quote


class CardFetcher:
    """カード情報を取得するクラス"""

    def __init__(self, url: str):
        """
        Args:
            url: WikiWikiページのURL
        """
        self.url = url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_page(self) -> Optional[BeautifulSoup]:
        """
        ページを取得してBeautifulSoupオブジェクトを返す

        Returns:
            BeautifulSoupオブジェクト、失敗時はNone
        """
        try:
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()

            # WikiWikiはShift_JISの可能性があるため、エンコーディングを適切に設定
            if 'charset' in response.headers.get('Content-Type', ''):
                response.encoding = response.encoding
            else:
                # Shift_JISを試す
                try:
                    response.encoding = 'shift_jis'
                    _ = response.text  # デコードテスト
                except:
                    response.encoding = response.apparent_encoding

            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as e:
            print(f"ページの取得に失敗しました: {e}")
            return None

    def find_card_table(self, soup: BeautifulSoup) -> Optional[any]:
        """
        「実装カード一覧」の表を見つける

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            テーブル要素、見つからない場合はNone
        """
        # ページ内の全てのテーブルを検索
        tables = soup.find_all('table')

        for table in tables:
            # ヘッダー行を取得
            headers = table.find_all('th')
            header_texts = [th.get_text(strip=True) for th in headers]

            # 実装カード一覧の特徴的なヘッダーをチェック
            # 「レアリティ」「カード名」「初出ガチャ」などが含まれているか確認
            required_headers = ['レアリティ', 'カード名']
            optional_headers = ['初出ガチャ', 'スマイル', 'ピュア', 'クール']

            has_required = all(h in header_texts for h in required_headers)
            has_optional = any(h in header_texts for h in optional_headers)

            if has_required and has_optional:
                return table

            # または「実装カード一覧」という見出しの後のテーブルかチェック
            prev_heading = table.find_previous(['h2', 'h3', 'h4'])
            if prev_heading:
                heading_text = prev_heading.get_text(strip=True)
                if '実装カード' in heading_text or 'カード一覧' in heading_text:
                    return table

        return None

    def parse_card_table(self, table) -> List[Dict[str, str]]:
        """
        カードテーブルをパースしてデータを抽出

        Args:
            table: テーブル要素

        Returns:
            カード情報の辞書のリスト
        """
        cards = []

        # ヘッダー行を取得
        headers = []
        header_row = table.find('tr')
        if header_row:
            for th in header_row.find_all(['th', 'td']):
                headers.append(th.get_text(strip=True))

        if not headers:
            print("ヘッダーが見つかりませんでした")
            return cards

        print(f"検出されたヘッダー: {headers}")

        # データ行を処理
        rows = table.find_all('tr')[1:]  # ヘッダー行をスキップ
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) == 0:
                continue

            card_data = {}
            for i, cell in enumerate(cells):
                if i < len(headers):
                    header = headers[i]
                    value = cell.get_text(strip=True)
                    card_data[header] = value

            if card_data:
                cards.append(card_data)

        return cards

    def fetch_cards(self) -> List[Dict[str, str]]:
        """
        カード一覧を取得する

        Returns:
            カード情報の辞書のリスト
        """
        print(f"ページを取得中: {self.url}")
        soup = self.fetch_page()

        if not soup:
            return []

        print("実装カード一覧の表を検索中...")
        table = self.find_card_table(soup)

        if not table:
            print("実装カード一覧の表が見つかりませんでした")
            return []

        print("テーブルをパース中...")
        cards = self.parse_card_table(table)
        print(f"{len(cards)}件のカードが見つかりました")

        return cards


def generate_card_link(card_name: str, member_name: str = "藤島慈") -> str:
    """
    カード詳細ページへのリンクを生成

    Args:
        card_name: カード名
        member_name: メンバー名（デフォルトは「藤島慈」）

    Returns:
        カード詳細ページのURL
    """
    base_url = "https://wikiwiki.jp/llll_wiki/"

    # カード名内の半角記号を全角に変換
    card_name_converted = card_name.replace('/', '／')

    # カード名を全角[]で囲み、メンバー名を追加してURLエンコード
    page_name = f"［{card_name_converted}］{member_name}"
    encoded_name = quote(page_name.encode('utf-8'))
    return base_url + encoded_name


def save_to_csv(cards: List[Dict[str, str]], output_path: str, member_name: str = "藤島慈"):
    """
    カードデータをCSVファイルに保存

    Args:
        cards: カード情報の辞書のリスト
        output_path: 出力ファイルパス
        member_name: メンバー名
    """
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['メンバー', 'レアリティ', 'カード名', 'リンク']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        for card in cards:
            card_name = card.get('カード名', '')
            rarity = card.get('レアリティ', '')

            if not card_name:
                continue

            link = generate_card_link(card_name, member_name)

            writer.writerow({
                'メンバー': member_name,
                'レアリティ': rarity,
                'カード名': card_name,
                'リンク': link
            })

    print(f"CSVファイルを保存しました: {output_path}")


def main():
    """メイン関数"""
    url = "https://wikiwiki.jp/llll_wiki/%E8%93%AE%E3%83%8E%E7%A9%BA%E5%A5%B3%E5%AD%A6%E9%99%A2/%E4%B9%99%E5%AE%97%E6%A2%A2"
    member_name = "乙宗梢"
    output_path = f"data/card_link_{member_name}.csv"

    fetcher = CardFetcher(url)
    cards = fetcher.fetch_cards()

    if cards:
        print("\n取得したカードデータ:")
        print("-" * 80)
        for i, card in enumerate(cards[:5], 1):  # 最初の5件を表示
            print(f"\nカード {i}:")
            for key, value in card.items():
                print(f"  {key}: {value}")

        if len(cards) > 5:
            print(f"\n... 他 {len(cards) - 5} 件")

        # CSVに保存
        print(f"\nCSVファイルに保存中...")
        save_to_csv(cards, output_path, member_name)
    else:
        print("カードデータを取得できませんでした")


if __name__ == "__main__":
    main()
