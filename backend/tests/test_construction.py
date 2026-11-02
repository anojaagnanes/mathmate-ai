from app.construction import match_constructions, split_parts

SAMPLE = '''பின்வரும் கேத்திரகணித அமைப்புக்களுக்காக cm/mm அளவிடை உள்ள ஒரு நேர் விளிம்பையும்
ஒரு கவராயத்தையும் மாத்திரம் பயன்படுத்துக. அமைப்புக் கோடுகளை தெளிவாக காட்டுக.
i. AB =7cm,BC - 5cm, ABC - 903 ஆகவுள்ள முக்கோணி ABC ஐ அமைக்குக.
ii. A இலிருந்தும் B இலிருந்தும் சமதூரத்தில் உள்ள புள்ளிகளின் ஒழுக்கை அமைக்குக.
iii. பக்கம் BC ஐ B இல் தொட்டுச்செல்வதும் A இனூடாகச் செல்வதுமான வட்டத்தை அமைக்குக.
iv. C இலிருந்து வட்டத்திற்கு வரையக்கூடிய மற்றைய தொடலியை (BC தவிர்ந்த) அமைக்குக.'''


def test_sample_splits_into_four_labeled_parts():
    parts = split_parts(SAMPLE)
    assert [label for label, _ in parts] == ['i', 'ii', 'iii', 'iv']


def test_sample_matches_all_four_guides_with_values():
    guides = match_constructions(SAMPLE)
    assert [g['kind'] for g in guides] == ['triangle', 'perp_bisector', 'tangent_circle', 'external_tangent']
    assert guides[0]['given'] == 'AB = 7 cm, BC = 5 cm, ∠ABC = 90°'
    assert guides[0]['diagram']['right'] == '1'
    assert guides[1]['diagram'] == {'kind': 'perp_bisector', 'p1': 'A', 'p2': 'B'}
    assert guides[2]['diagram']['at'] == 'B' and guides[2]['diagram']['thru'] == 'A'
    assert guides[3]['diagram']['from'] == 'C' and guides[3]['diagram']['given'] == 'BC'
    for guide in guides:
        assert len(guide['steps']) >= 4 and guide['checks']
        for step in guide['steps']:
            assert step['en'] and step['ta'] and step['why_en'] and step['why_ta']


def test_hypotenuse_check_is_computed():
    guides = match_constructions('i. AB = 7cm, BC = 5cm, ABC = 90 construct triangle ABC.')
    assert '8.6 cm' in guides[0]['checks'][-1]['en']


def test_english_variants_match():
    assert match_constructions('Construct the locus of points equidistant from P and Q.')[0]['kind'] == 'perp_bisector'
    assert match_constructions('Construct a circle tangent to line BC at B through A.')[0]['kind'] == 'tangent_circle'
    assert match_constructions('Construct the other tangent from C to the circle.')[0]['kind'] == 'external_tangent'


def test_non_construction_text_returns_none():
    assert match_constructions('2x+3=11') is None
    assert match_constructions('find the area of a circle with radius 4') is None
    assert match_constructions('ஆரம் 4 உள்ள வட்டத்தின் பரப்பளவு காண்க') is None


def test_question_endpoint_serves_construction_route(client, auth):
    response = client.post('/api/v1/math/question', data={'question': SAMPLE, 'variable': '', 'intent': 'solve'}, headers=auth)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['route'] == 'construction' and body['status'] == 'solved'
    assert [g['kind'] for g in body['guides']] == ['triangle', 'perp_bisector', 'tangent_circle', 'external_tangent']
