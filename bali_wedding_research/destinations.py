from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DestinationConfig:
    id: str
    slug: str
    name_zh: str
    name_en: str
    eyebrow: str
    index_title: str
    detail_title_suffix: str
    hero_title: str
    hero_lede: str
    region_stat_label: str
    transfer_sort_label: str
    transfer_summary_label: str
    transport_risk_label: str
    style_intro: str
    root_card_copy: str


DESTINATIONS: dict[str, DestinationConfig] = {
    "bali": DestinationConfig(
        id="bali",
        slug="bali",
        name_zh="峇里島",
        name_en="Bali",
        eyebrow="Bali Island Wedding Lookbook",
        index_title="峇里島婚禮場地索引",
        detail_title_suffix="峇里島婚禮場地檔案",
        hero_title="峇里島婚禮場地不是清單，是場景選擇",
        hero_lede=(
            "把峇里島婚禮拆成教堂、叢林、水台、懸崖、沙灘與室內宴會。"
            "首頁先讓你看風格與場景，真的有興趣再進飯店頁看價格、雨備、交通與照片。"
        ),
        region_stat_label="峇里區域",
        transfer_sort_label="距機場最短",
        transfer_summary_label="距機場約",
        transport_risk_label="交通風險",
        style_intro="先用畫面決定你要哪一種峇里島婚禮，再進場地頁看細節。",
        root_card_copy="懸崖、教堂、叢林、水台與海邊晚宴，適合先看婚禮風格再縮小場地。",
    ),
    "maldives": DestinationConfig(
        id="maldives",
        slug="maldives",
        name_zh="馬爾地夫",
        name_en="Maldives",
        eyebrow="Maldives Island Wedding Lookbook",
        index_title="馬爾地夫婚禮飯店索引",
        detail_title_suffix="馬爾地夫婚禮飯店檔案",
        hero_title="馬爾地夫婚禮先選島，再選儀式場景",
        hero_lede=(
            "馬爾地夫不是一般城市型場地比較；每一間飯店都是一座島。"
            "這裡用水上亭、沙洲、白沙灘、潟湖晚宴、雨備與接駁方式，幫你先判斷哪座島真的適合辦婚禮。"
        ),
        region_stat_label="環礁區域",
        transfer_sort_label="接駁最短",
        transfer_summary_label="MLE 接駁約",
        transport_risk_label="接駁風險",
        style_intro="先用水上、沙洲、白沙灘與潟湖場景分流，再比較接駁與雨備。",
        root_card_copy="水上亭、白沙灘、私人沙洲與潟湖晚宴，適合重視私密感與海島儀式感的新人。",
    ),
}


def get_destination_config(destination_id: str) -> DestinationConfig:
    try:
        return DESTINATIONS[destination_id]
    except KeyError as exc:
        available = ", ".join(sorted(DESTINATIONS))
        raise ValueError(f"unsupported destination: {destination_id}; expected one of {available}") from exc


def destination_ids() -> list[str]:
    return list(DESTINATIONS)
