import pandas as pd
import numpy as np
import datetime
import gradio as gr
from flask import Flask, render_template, request, jsonify
import threading
import webbrowser

class EnergyPolicyPredictor:
    def __init__(self):
        self.base_production = 1000
        self.simulation_history = []

    def predict_energy(self, interest_rate, season, gdp_growth,
                      oil_price, tech_investment, policy_mode='neutral'):
        """정책 모드별 예측 로직"""
        production = self.base_production

        # 정책 모드별 가중치 설정
        if policy_mode == 'eco':
            # 친환경 정책 모드
            interest_weight = 0.015
            gdp_weight = 0.04
            oil_weight = 0.7
            tech_weight = 0.5
            green_bonus = 1.2
            efficiency_bonus = 1.1

        elif policy_mode == 'non_eco':
            # 비친환경 정책 모드
            interest_weight = 0.025
            gdp_weight = 0.02
            oil_weight = 0.3
            tech_weight = 0.2
            green_bonus = 0.8
            efficiency_bonus = 0.9

        else:  # neutral
            # 중립 모드
            interest_weight = 0.02
            gdp_weight = 0.03
            oil_weight = 0.5
            tech_weight = 0.3
            green_bonus = 1.0
            efficiency_bonus = 1.0

        # 기본 효과 계산
        production *= (1 - interest_weight * interest_rate)
        production *= (1 + gdp_weight * gdp_growth)

        oil_effect = (oil_price - 60) / 60 * oil_weight
        production *= (1 + oil_effect)

        tech_effect = (tech_investment - 100) / 100 * tech_weight
        production *= (1 + tech_effect)

        # 정책 효과 적용
        production *= green_bonus
        production *= efficiency_bonus

        # 계절성 효과 추가
        if season == '여름':
            production *= 1.15
        elif season == '겨울':
            production *= 0.85
        elif season == '봄/가을':
            production *= 1.0

        return max(0, production)

    def run_simulation(self, interest_rate, season, gdp_growth,
                      oil_price, tech_investment, policy_mode='neutral'):
        """시뮬레이션 실행"""
        try:
            prediction = self.predict_energy(
                interest_rate, season, gdp_growth,
                oil_price, tech_investment,
                policy_mode
            )

            return f"{prediction:.1f} TOE"

        except Exception as e:
            return f"시뮬레이션 오류: {str(e)}"

def create_gradio_interface():
    model = EnergyPolicyPredictor()

    with gr.Blocks(title="재생에너지 생산량 예측기") as interface:
        gr.Markdown("# 재생에너지 생산량 시뮬레이션")

        with gr.Row():
            with gr.Column():
                gr.Markdown("## 기준 금리")

                interest = gr.Slider(
                    minimum=0, maximum=10, value=3.5,
                    label="기준금리 (%)",
                    info="에너지 정책의 핵심 변수"
                )

                gr.Markdown("## 다른 변동 요인")
                
                season = gr.Radio(
                    choices=['봄/가을', '여름', '겨울'],
                    value='봄/가을',
                    label="계절 선택"
                )

                policy_mode = gr.Radio(
                    choices=['eco', 'neutral', 'non_eco'],
                    value='neutral',
                    label="정책 모드 선택",
                    info="탄소중립 / 기본 / 비탄소중립"
                )

                gdp = gr.Slider(
                    minimum=-5, maximum=10, value=2.5,
                    label="GDP 성장률 (%)"
                )
                oil = gr.Slider(
                    minimum=20, maximum=150, value=60,
                    label="유가 (달러)"
                )
                tech = gr.Slider(
                    minimum=50, maximum=200, value=100,
                    label="기술 투자 지수"
                )

                predict_btn = gr.Button("시뮬레이션 실행")

            with gr.Column():
                output_text = gr.Textbox(label="예측된 재생에너지 생산량 (TOE)")

        predict_btn.click(
            fn=model.run_simulation,
            inputs=[interest, season, gdp, oil, tech, policy_mode],
            outputs=[output_text]
        )

    return interface

# Flask 애플리케이션 생성
app = Flask(__name__)
energy_model = EnergyPolicyPredictor()

# Flask 라우트 설정
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    prediction = energy_model.run_simulation(
        interest_rate=data.get('interest_rate', 3.5),
        season=data.get('season', '봄/가을'),
        gdp_growth=data.get('gdp_growth', 2.5),
        oil_price=data.get('oil_price', 60),
        tech_investment=data.get('tech_investment', 100),
        policy_mode=data.get('policy_mode', 'neutral')
    )
    return jsonify({'prediction': prediction})

# HTML 템플릿 생성 함수
def create_html_template():
    html_content = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>재생에너지 생산량 예측기</title>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .input-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; }
        input[type="range"] { width: 100%; }
        select { width: 100%; padding: 5px; }
        #prediction { margin-top: 20px; font-weight: bold; }
    </style>
</head>
<body>
    <h1>재생에너지 생산량 시뮬레이션</h1>
    
    <div class="input-group">
        <label for="interest_rate">기준금리 (%)</label>
        <input type="range" id="interest_rate" min="0" max="10" value="3.5" step="0.1">
        <span id="interest_rate_value">3.5</span>%
    </div>

    <h2>다른 변동 요인</h2>

    <div class="input-group">
        <label for="season">계절 선택</label>
        <select id="season">
            <option value="봄/가을">봄/가을</option>
            <option value="여름">여름</option>
            <option value="겨울">겨울</option>
        </select>
    </div>

    <div class="input-group">
        <label for="policy_mode">정책 모드 선택</label>
        <select id="policy_mode">
            <option value="neutral">중립</option>
            <option value="eco">친환경</option>
            <option value="non_eco">비친환경</option>
        </select>
    </div>

    <div class="input-group">
        <label for="gdp_growth">GDP 성장률 (%)</label>
        <input type="range" id="gdp_growth" min="-5" max="10" value="2.5" step="0.1">
        <span id="gdp_growth_value">2.5</span>%
    </div>

    <div class="input-group">
        <label for="oil_price">유가 (달러)</label>
        <input type="range" id="oil_price" min="20" max="150" value="60" step="1">
        <span id="oil_price_value">60</span>
    </div>

    <div class="input-group">
        <label for="tech_investment">기술 투자 지수</label>
        <input type="range" id="tech_investment" min="50" max="200" value="100" step="1">
        <span id="tech_investment_value">100</span>
    </div>

    <button onclick="predict()">시뮬레이션 실행</button>

    <div id="prediction"></div>

    <script>
        // 슬라이더 값 실시간 표시
        ['interest_rate', 'gdp_growth', 'oil_price', 'tech_investment'].forEach(id => {
            const slider = document.getElementById(id);
            const valueSpan = document.getElementById(id + '_value');
            slider.addEventListener('input', () => {
                valueSpan.textContent = slider.value;
            });
        });

        function predict() {
            const data = {
                interest_rate: parseFloat(document.getElementById('interest_rate').value),
                season: document.getElementById('season').value,
                policy_mode: document.getElementById('policy_mode').value,
                gdp_growth: parseFloat(document.getElementById('gdp_growth').value),
                oil_price: parseFloat(document.getElementById('oil_price').value),
                tech_investment: parseFloat(document.getElementById('tech_investment').value)
            };

            axios.post('/predict', data)
                .then(response => {
                    document.getElementById('prediction').textContent = 
                        '예측된 재생에너지 생산량: ' + response.data.prediction;
                })
                .catch(error => {
                    console.error('Error:', error);
                    document.getElementById('prediction').textContent = 
                        '예측 오류: ' + error.message;
                });
        }
    </script>
</body>
</html>
    '''
    
    # templates 폴더 생성
    import os
    os.makedirs('templates', exist_ok=True)
    
    # HTML 파일 저장
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

# 메인 함수 (Gradio와 Flask 동시 실행)
def main():
    # HTML 템플릿 생성
    create_html_template()

    # Gradio 인터페이스 생성
    gradio_interface = create_gradio_interface()

    # Flask 서버 스레드 시작
    def run_flask():
        app.run(host='0.0.0.0', port=5000)

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Gradio 인터페이스 실행
    gradio_interface.launch(share=True, server_name='0.0.0.0')

if __name__ == "__main__":
    main()
