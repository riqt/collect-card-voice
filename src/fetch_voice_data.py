import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re


def extract_voice_data(url):
    """URLから演出・ボイスセクションのデータを抽出"""
    try:
        print(f"Processing: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        # 演出・ボイスセクションを探す
        voice_data = {
            '入手時': '',
            '特訓時': '',
            '特訓1回目': '',
            '特訓2回目': '',
            'ライブ開始': '',
            'スキル発動': '',
            'スキル発動(クロスボイス)': '',
            'SP発動': ''
        }

        # h2タグで「演出・ボイス」を探す
        headers = soup.find_all(['h2', 'h3', 'h4'])
        voice_section = None

        for header in headers:
            if '演出' in header.get_text() and 'ボイス' in header.get_text():
                voice_section = header
                break

        if not voice_section:
            print(f"  Warning: 演出・ボイス section not found for {url}")
            return voice_data

        # 次のdivを探す
        div = voice_section.find_next_sibling('div')
        if div:
            # div内のテーブルを探す
            table = div.find('table')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['th', 'td'])
                    if len(cells) >= 2:
                        type_text = cells[0].get_text().strip()
                        message_text = cells[1].get_text().strip()

                        # 各カテゴリにマッチング
                        if '入手時' in type_text:
                            voice_data['入手時'] = message_text
                        elif '特訓1回目' in type_text:
                            voice_data['特訓1回目'] = message_text
                        elif '特訓2回目' in type_text:
                            voice_data['特訓2回目'] = message_text
                        elif '特訓時' in type_text:
                            voice_data['特訓時'] = message_text
                        elif 'ライブ開始' in type_text:
                            voice_data['ライブ開始'] = message_text
                        elif 'クロスボイス' in type_text:
                            voice_data['スキル発動(クロスボイス)'] = message_text
                        elif 'スキル発動' in type_text and not voice_data['スキル発動']:
                            voice_data['スキル発動'] = message_text
                        elif 'SP発動' in type_text or 'SP スキル発動' in type_text:
                            voice_data['SP発動'] = message_text

        print(f"  Extracted: {sum(1 for v in voice_data.values() if v)} voice entries")
        return voice_data

    except Exception as e:
        print(f"  Error processing {url}: {e}")
        return {
            '入手時': '',
            '特訓時': '',
            '特訓1回目': '',
            '特訓2回目': '',
            'ライブ開始': '',
            'スキル発動': '',
            'スキル発動(クロスボイス)': '',
            'SP発動': ''
        }


def extract_voice_text(element, voice_type):
    """要素からボイステキストを抽出"""
    text = element.get_text()

    # テーブルの場合
    if element.name == 'table':
        rows = element.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                header = cells[0].get_text().strip()
                if voice_type in header:
                    return cells[1].get_text().strip()

    # リストや段落の場合
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if voice_type in line:
            # 同じ行または次の行からテキストを抽出
            content = line.replace(voice_type, '').strip()
            if content and content not in ['', ':', '：']:
                # 不要な記号を削除
                content = re.sub(r'^[:\s：]+', '', content)
                return content
            elif i + 1 < len(lines):
                content = lines[i + 1].strip()
                content = re.sub(r'^[:\s：]+', '', content)
                if content:
                    return content

    return ''


def main():
    member_name = "乙宗梢"
    csv_path = f'data/card_link_{member_name}.csv'
    output_path = f'data/card_link_with_voices_{member_name}.csv'

    # CSVを読み込む
    print(f"Reading CSV from {csv_path}")
    df = pd.read_csv(csv_path)

    # 新しいカラムを初期化
    df['入手時'] = ''
    df['特訓時'] = ''
    df['特訓1回目'] = ''
    df['特訓2回目'] = ''
    df['ライブ開始'] = ''
    df['スキル発動'] = ''
    df['スキル発動(クロスボイス)'] = ''
    df['SP発動'] = ''

    # 各行を処理
    for index, row in df.iterrows():
        url = row['リンク']
        voice_data = extract_voice_data(url)

        # データを更新
        for key, value in voice_data.items():
            df.at[index, key] = value

        # サーバーに負荷をかけないよう待機
        time.sleep(1)

    # CSVに保存
    print(f"\nSaving to {output_path}")
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print("Done!")


if __name__ == "__main__":
    main()
