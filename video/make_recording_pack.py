"""Generate the current team scripts and editor handoff from the canonical story."""
from pathlib import Path
import csv
import json
import zipfile

from v2_story import PEOPLE, ROOT, RUNTIME_S, scenes

DEST = ROOT / 'video/team-kit/v2-audio-first'
BUILD = ROOT / 'video/build/v3'


def timecode(n):
    return f'{n // 60}:{n % 60:02d}'


def generate():
    DEST.mkdir(parents=True, exist_ok=True)
    shots = scenes()
    shared = [s for s in shots if s['speaker'] == 'all']
    directions = '''錄音安排

先理解自己每段的意思，再用自然語速錄製。每個 scene 錄成一個完整音檔，每段兩個 take。安靜房間、同一支手機或麥克風；開始及結束各留 1–2 秒，保留原始 m4a/wav，不加音樂。

畫面時間只是參考。Ean 會按真人聲音調整剪接和字幕，不必追着參考旁白的秒數。
個人出鏡是選擇性的，其餘可以旁白配產品畫面。現行分鏡有三段共同出鏡／台詞：N01 開場、N04 完整核心問題、N17 結尾，可同一機位一次錄齊。凡嘴部入鏡，畫面和聲音一起錄，避免對嘴問題。
如只拍兩段共同出鏡，可保留 N01/N04，N17 由 Ean 用字卡配四人合聲；先保留這三段台詞。

'''
    for key, person in PEOPLE.items():
        text = f"{person['alias']} — {person['name']}\n最新分工：{person['focus_zh']}\n\n" + directions
        text += '個人場次（每場一個音檔）\n'
        for shot in shots:
            if shot['speaker'] != key:
                continue
            text += f"\n{shot['id']} — {shot['title']}\n參考位置：{timecode(shot['start_s'])}–{timecode(shot['end_s'])}\n檔名：{person['alias']}_{shot['id']}_take1.m4a\n\n{shot['narration']}\n"
        text += '\n共同台詞（四人一起練習及錄製）\n'
        for shot in shared:
            text += f"\n{shot['id']}: {shot['narration']}\n"
        if key == 'ieong':
            text += '\nN15 Melbourne：旁白只說預先登記測試的固定事實，沒有宣稱測試已完成或有效。畫面暫為 pending。有可用結果後，另補圖表或短旁白即可，不需要現在等待結果才錄。\n'
        (DEST / f"{person['name'].replace(' ', '_')}.txt").write_text(text)
    roster = '\n'.join(f"{p['alias']} ({p['name']})：{p['focus_zh']}。" for p in PEOPLE.values())
    intro = f'''CrowdPulse Macau — 最新錄音與剪輯安排（2026-10-20）

項目主軸：手機在本機計數，只傳數值；CrowdPulse 顯示人潮預測、信心與原因，再讓工作人員審閱和決定。缺少路線證據時，改道批准會被阻擋，可申請現場核查或拒絕。申請核查不等於已完成檢查。

方案模擬是 CrowdPulse 的一個功能，用街道模型比較方案對不同使用者的影響，對外不另作一個產品介紹。模型結果不是實地路線認證。影片中的人物統一是一位匿名輪椅使用者的示意情境。

目前有可操作原型、測試與 {timecode(RUNTIME_S)} 參考影片。澳門人潮預測畫面為模擬；新審批示範是預先設定的模擬測試輸入，操作及 API 執行是真的。尚未完成澳門實地驗證。

最新分工（本包取代先前錄音稿）
{roster}

{directions}
Melbourne 測試窗至 10/22 21:00 港澳時間才結束，之後需資料同步與核對。這兩天先錄音和需要的鏡頭；N15 可先照本包錄，結果另作短插入。不要把測試已登記說成測試已通過。

已移除右下角 Guide audio 字樣，參考片目前仍是合成聲音。真人音軌尚未加入。圖中的 Camera placeholders 會在換上真實鏡頭時一併移除。學校及成人督導資料仍需在提交表確認。
'''
    (DEST / 'START_HERE_項目介紹與錄音安排.txt').write_text(intro)
    handoff = '''Ean — 剪輯交接

主畫面檔：crowdpulse_v3_picture_only_1080p.mp4
此檔無音軌、無燒錄旁白字幕，保留產品畫面、姓名分工、來源／模擬標示和三段團隊鏡頭佔位。不要把它當作已完成真人版。

參考片：GUIDE_PREVIEW.mp4（有合成聲音及參考字幕）。
字幕檔：crowdpulse_v3_guide_captions.srt（只供起步，要按真人聲音重新對時）。
場次表：scene-timeline.csv（標明每場開始、結束、發言人及全文）。

1. 以真人錄音為準調整畫面停頓和字幕，保持全片在比賽時限內，不要為卡原時間而壓快發言。
2. N01/N04/N17 是三段共同台詞，可一次錄齊。個人出鏡可放在本人負責內容開頭，其餘使用旁白和產品畫面。
3. 如只用兩段四人出鏡，保留 N01/N04；N17 改用 CrowdPulse 字卡與四人合聲。共同核心問題必須完整說出。
4. 新 N09 是『未核實 → 批准被阻擋 → 請求核查 → 拒絕 → 紀錄』。不要換回舊 APPROVE 改道畫面。保留 seeded/simulated、self-declared 和 request is not an inspection 的資料界線。
5. 人物統一稱為匿名輪椅使用者的示意情境。方案模擬是 CrowdPulse 的一個功能，不另作產品主軸。
6. N15 的旁白是預先登記測試的固定事實，pending 在畫面。若有經核對的 Melbourne 結果，可以更新這場圖表或補一句旁白，不需要其他人重錄。
7. 換上真人鏡頭時移除該場 Camera placeholders 標示；保持模型／示意／資料來源標示。學校與成人督導資料在提交表另外確認，不可自行填假資料。
'''
    (DEST / 'Ean_剪輯交接.txt').write_text(handoff)
    with (DEST / 'scene-timeline.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['scene','start_seconds','end_seconds','start_time','end_time','speaker','dialogue'])
        for shot in shots:
            person = PEOPLE.get(shot['speaker'])
            writer.writerow([shot['id'],shot['start_s'],shot['end_s'],timecode(shot['start_s']),timecode(shot['end_s']),person['alias'] if person else shot['speaker'],shot['narration']])
    # Verify the actual per-person files, not only the metadata used to generate them.
    for shot in shots:
        if shot['speaker'] in PEOPLE:
            person = PEOPLE[shot['speaker']]
            assert shot['narration'] in (DEST / f"{person['name'].replace(' ', '_')}.txt").read_text()
    assert 'N11 —' not in (DEST/'Yeung_Hou_Sam.txt').read_text()
    assert 'N11 —' in (DEST/'Wong_U_Hei.txt').read_text()
    assert all('Mrs Chan' not in p.read_text() for p in DEST.glob('*.txt') )
    return shots


def package():
    generate()
    cut = BUILD / 'cut'
    preview = cut/'crowdpulse_v3_full_preview_720p.mp4'
    audio_pack = BUILD/'CrowdPulse_錄音包_v3_2026-10-20.zip'
    editor_pack = BUILD/'CrowdPulse_Ean剪輯包_v3_2026-10-20.zip'
    common = list(DEST.glob('*.txt')) + [DEST/'scene-timeline.csv']
    for archive, editing in [(audio_pack,False),(editor_pack,True)]:
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for p in common:z.write(p,p.name)
            z.write(preview,'GUIDE_PREVIEW.mp4',compress_type=zipfile.ZIP_STORED)
            if editing:
                z.write(cut/'crowdpulse_v3_picture_only_1080p.mp4','crowdpulse_v3_picture_only_1080p.mp4',compress_type=zipfile.ZIP_STORED)
                z.write(cut/'crowdpulse_v3_guide_captions.srt','crowdpulse_v3_guide_captions.srt')
        with zipfile.ZipFile(archive) as z:assert z.testzip() is None
        print(archive)


if __name__ == '__main__':
    package()
