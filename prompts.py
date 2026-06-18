import json


def palm_prompt(dominant_hand: str, report_name: str, tone: str) -> str:
    return f"""
너는 손금 해석을 친절하게 설명하는 에디토리얼 리포트 작가이다.
사용자가 업로드한 왼손/오른손 사진을 실제로 관찰하고 손금 리포트를 작성하라.

중요 안전 원칙:
- 손금 해석은 과학적 진단이나 확정적 예언이 아니라 상징적 성향 분석이라고 분명히 말하라.
- 건강, 수명, 질병, 사고, 임신, 재산, 죽음 등을 단정하거나 예언하지 마라.
- 사진에서 보이는 선의 흐름, 깊이, 끊김, 방향만 근거로 말하라.
- 특정 개인의 신원이나 민감한 속성은 추정하지 마라.

리포트 설정:
- 리포트 이름: {report_name}
- 주로 사용하는 손: {dominant_hand}
- 문체: {tone}

친절한 구성:
1. 제목
2. 먼저 읽어주세요
3. 사진에서 보이는 전체 인상
4. 왼손: 타고난 기질과 내면의 흐름
   - 생명선: 보이는 특징 / 쉽게 풀이 / 생활 팁
   - 두뇌선: 보이는 특징 / 쉽게 풀이 / 생활 팁
   - 감정선: 보이는 특징 / 쉽게 풀이 / 관계 팁
   - 운명선: 보이는 특징 / 쉽게 풀이 / 일과 방향 팁
   - 태양선: 보이는 특징 / 쉽게 풀이 / 재능 활용 팁
5. 오른손: 현재의 선택과 사회적 모습
   - 생명선, 두뇌선, 감정선, 운명선, 태양선 동일 구성
6. 양손 비교: 타고난 성향과 현재 모습의 차이
7. 핵심 성향 카드 5개: LIFE, MIND, HEART, WORK, TALENT
8. 나에게 해주면 좋은 조언 5가지
9. 한 줄 리딩

각 항목은 초보자가 이해할 수 있게 친절하고 구체적으로 작성하라.
단, 과장된 점술 말투가 아니라 고급 매거진의 차분한 분석 문체를 사용하라.
"""


def photo_analysis_prompt(mode, subject_type, style, output_use, extra_request):
    schema = {
        "scene_summary": "사진 속 실제 장면 요약",
        "composition_type": "사진의 구도 유형",
        "visual_flow": "시선 흐름 설명",
        "light_direction": "빛의 방향과 활용 방법",
        "background_notes": "배경에서 주의할 요소",
        "recommended_crop": {
            "left_percent": 10,
            "top_percent": 8,
            "right_percent": 88,
            "bottom_percent": 96,
            "aspect_ratio": "4:5",
            "reason": "이 영역만 사용해도 장면의 핵심이 살아나고 불필요한 주변부가 줄어듭니다."
        },
        "best_positions": [
            {
                "rank": 1,
                "short_label": "짧은 위치 이름",
                "x_percent": 68,
                "y_percent": 64,
                "pose": "추천 포즈 또는 피사체 배치 방식",
                "camera_tip": "카메라 거리, 높이, 각도 팁",
                "reason": "사진 속 실제 요소를 근거로 이 위치가 좋은 이유"
            }
        ],
        "avoid_positions": [{"x_percent": 50, "y_percent": 42, "reason": "피해야 하는 이유"}],
        "shooting_tips": ["실제 촬영 팁 1", "실제 촬영 팁 2", "실제 촬영 팁 3"],
        "one_line_direction": "촬영자가 바로 말해줄 수 있는 한 줄 디렉팅"
    }
    return f"""
너는 전문 사진 디렉터이자 구도 분석가이다.
업로드한 사진을 실제로 관찰하여, {subject_type}이(가) 어디에 배치되면 가장 자연스럽고 아름다운지 분석하라.

중요:
- 하드코딩된 일반 조언을 하지 마라. 반드시 사진 속 실제 장면을 근거로 분석하라.
- 사진 속 공간, 선, 여백, 빛 방향, 배경 요소, 시선 흐름을 관찰하라.
- 추천 위치는 이미지 전체 기준의 비율 좌표로 제시하라.
- x_percent는 왼쪽 0, 오른쪽 100이다.
- y_percent는 위쪽 0, 아래쪽 100이다.
- 좌표는 모델의 몸 중심 또는 피사체 중심이 놓일 지점이다.
- 사진 전체를 다 쓰지 않아도 된다. 더 좋은 결과를 위해 일부만 잘라 쓰는 편이 좋다면 recommended_crop을 적극적으로 제안하라.
- recommended_crop은 최종 예시 이미지에 사용할 최적 크롭 영역이다. left_percent < right_percent, top_percent < bottom_percent를 지켜라.
- recommended_crop은 장면의 핵심이 살아나는 구도를 만들어야 하며, 불필요한 빈 공간이나 산만한 주변부를 줄여야 한다.
- best_positions는 원본 전체 사진 좌표 기준으로 3개를 반환하라.
- 특정 인물의 신원, 나이, 성별, 민감한 속성은 추정하지 마라.
- 결과는 JSON만 반환하라.

사용자 설정:
- 분석 모드: {mode}
- 배치할 대상: {subject_type}
- 원하는 분위기: {style}
- 결과물 용도: {output_use}
- 추가 요청: {extra_request}

반환 JSON 스키마:
{json.dumps(schema, ensure_ascii=False, indent=2)}

best_positions는 반드시 3개를 반환하라. recommended_crop도 반드시 반환하라.
"""


def image_edit_prompt(analysis: dict, subject_type: str, style: str, extra_request: str) -> str:
    best = (analysis.get("best_positions") or [{}])[0]
    crop = analysis.get("recommended_crop") or {}
    crop_note = ""
    if crop:
        crop_note = f"The base image may already be a cropped composition. Respect that cropped framing and keep the subject inside it. Crop reason: {crop.get('reason', '')}"
    return f"""
EDIT THE UPLOADED PHOTO. Do not create a different scene.

Goal:
Place one realistic {subject_type} in the exact recommended position so it looks like the model was really there during the shoot.

Placement:
- Put the model's body center around x={best.get('x_percent', 50)}%, y={best.get('y_percent', 62)}% of the image.
- Location label: {best.get('short_label', '')}
- Reason: {best.get('reason', '')}

Pose:
- {best.get('pose', '')}

Photorealism requirements:
- Preserve the original background, lens perspective, camera angle, depth, and lighting.
- Match the model scale to the scene.
- Add natural contact shadows and realistic ambient light on the model.
- Make the model stand on the existing ground plane or spatial surface.
- Respect occlusion: the model should be behind/around foreground objects if needed.
- No floating, no cut-out sticker look, no collage look.
- No text, no labels, no arrows, no markers.
- {crop_note}

Style:
- {style}
- realistic editorial photography, natural expression, premium but subtle.

Extra request:
{extra_request}
"""
