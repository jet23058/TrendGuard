# Project Rules & Operational Standards

## 1. Security & Configuration (ZERO TOLERANCE)
**Rule: No Hardcoded Secrets.**
- **Environment Variables**: ALL sensitive data (API Keys, tokens, passwords, database URLs, client_secrets) MUST be loaded from a `.env` file.
- **Implementation**:
  - Use `os.getenv('KEY_NAME')` or `python-dotenv` for Python.
  - Never assign actual secret strings to variables in source code.
- **Git Safety**:
  - Verify that `.env` is listed in `.gitignore`.
  - Do not commit any file containing real credentials.

## 2. Testing Protocol (HIGHEST PRIORITY)
**Rule: No Code Without Tests & Verification.**
Every time you generate or modify code, you MUST follow this strict SOP:

- **1. Code & Test Generation**:
  - **New Features**: Create a corresponding unit test file (e.g., `tests/test_feature.py`) covering happy paths and edge cases.
  - **Modifications**: Update existing tests to align with logic changes.
  - **Bug Fixes**: Create a regression test that fails before the fix and passes after the fix.

- **2. Execution & Self-Verification**:
  - **Mandatory Run**: After implementing code and tests, you must execute (or simulate the execution of) the testing suite.
  - **Result Validation**: Explicitly verify that the current output results are normal and match the expected behavior.
  - **Completion Criteria**: Do not consider a task "Complete" until you have successfully generated tests, verified they pass, and confirmed the output logic is correct.

## 3. Documentation Maintenance
**Rule: Keep documentation synchronized with code.**
- **Trigger**: Post-coding phase.
- **CHANGELOG.md**:
   - Append a new entry under the current date.
   - Format: `- [Type] Description of change (File modified)`
   - Types: Feat, Fix, Refactor, Test, Docs, Security.
- **README.md**:
   - If the code change affects usage, arguments, or installation (especially new `.env` variables), update the relevant section immediately.

## 4. Compliance & Terminology (Taiwan Regulations)
**Rule: Neutral Tool Positioning (NO Investment Advice).**
為符合台灣金融法規（如證券投資信託及顧問法），系統僅作為「輔助運算工具」，嚴禁出現引導交易、保證獲利或投資建議之用語。

- **1. Terminology Sanitization (用語中性化)**:
  - **禁止使用 (Banned)**: 停損 (Stop Loss)、停利 (Take Profit)、買進/賣出訊號 (Buy/Sell Signal)、建議 (Recommendation)、目標價 (Target Price)、飆股 (Soaring Stock)。
  - **強制替換 (Mandatory Replacement)**:
    - `停損` → **「風險控管點 (Risk Control Point)」** 或 **「下限觸發條件 (Lower Limit Trigger)」**
    - `停利` → **「條件滿足點 (Condition Met Point)」** 或 **「出場設定 (Exit Setting)」**
    - `訊號` → **「指標狀態 (Indicator Status)」** 或 **「篩選結果 (Filter Result)」**
    - `建議` → **「運算結果 (Calculation Result)」**
  
- **2. UI/UX Disclaimers (介面警語)**:
  - 系統啟動或產生報表時，必須包含免責聲明：
  > 「本系統僅提供數據運算與客觀條件篩選功能，不提供任何投資建議。使用者應自行判斷風險，過往數據不代表未來績效。」
  
- **3. Logic Neutrality (邏輯中立性)**:
  - 程式碼變數命名應避免意圖導向。
  - **Bad**: `def generate_buy_signal():`
  - **Good**: `def check_indicator_conditions():`
  - 系統不得主動發送「現在買進」的通知，僅能發送「條件已達成」的客觀通知。

### 用語替換對照表 (Quick Reference)

| 概念 | ❌ 嚴禁使用 (Illegal/Risky) | ✅ 規範用語 (Compliant) |
| :--- | :--- | :--- |
| **損失控制** | 停損 (Stop Loss) | 風險觸發價、觸發下限、防護設定 |
| **獲利了結** | 停利 (Take Profit) | 目標觸發價、觸發上限、區間設定 |
| **交易指示** | 買進訊號 (Buy Signal) | 多方條件成立、指標黃金交叉 |
| **交易指示** | 賣出訊號 (Sell Signal) | 空方條件成立、指標死亡交叉 |
| **預測** | 目標價 (Target Price) | 參考區間、壓力支撐運算值 |
| **性質** | 投資建議 (Advice) | 數據分析結果、策略回測數據 |