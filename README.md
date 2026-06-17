# 圖書館管理系統 (Library Management System)

資料庫系統管理期末報告 — Phase 2 系統實作

## 啟動方式

### 1. 安裝 Django
```bash
pip install "django>=3.2"
```

### 2. 建立資料庫
```bash
python manage.py migrate
```

### 3. 匯入同學提供的資料（必跑）
```bash
python load_classmate_data.py
```

### 4. 啟動伺服器
```bash
python manage.py runserver
```

開瀏覽器訪問 http://127.0.0.1:8000/

## 預設帳號

執行 `load_classmate_data.py` 後可用：

**讀者帳號（密碼都是 1234）：**
| 帳號 | 姓名 | 狀態 |
| --- | --- | --- |
| daming | 王大明 | 正常 |
| hsiaohua | 李小華 | 正常 |
| jianguo | 陳建國 | 正常 |
| yating | 林雅婷 | **停權（測試無法登入）** |
| elvan | 李采茜 | 正常 |
| david | 林木田 | 正常 |
| beauty | 張美麗 | 正常 |
| mary | 黃珠文 | 正常 |
| goan | 邱諒金 | 正常 |
| john | 高先進 | 正常 |

**管理員帳號：** `admin` / `admin123`

## 系統內容（匯入後）

- 30 本書（資訊、歷史、文學、心理、經濟、企管、理財、科普）
- 50 個副本
- 15 筆借閱記錄（11 筆借閱中 + 4 筆歷史）
- 5 筆預約記錄

## 功能列表

### 讀者端
- 首頁（含熱門書籍跑馬燈）
- 會員申請 / 會員登入 / 登出
- 書籍查找（依書名/作者/ISBN/分類）
- 書籍資訊（含借書、預約按鈕）
- 個人借閱資訊（含還書、借閱歷史紀錄）

### 管理員端
- 管理書籍（新增/編輯/刪除）
- 管理副本
- 查看所有借閱記錄

## 資料庫架構（對應期中報告 Phase 1）

| 期中 schema | Django Model | 說明 |
| --- | --- | --- |
| USER | UserProfile + User | 使用者，phone/state 放在 UserProfile |
| BOOK | Book | ISBN 為主鍵 |
| COPY | Copy | 一本書多個實體副本 |
| LOAN | Loan | 借閱記錄 |
| RESERVATION | Reservation | 預約記錄 |
| SEARCH_LOG | SearchLog | 搜尋紀錄（解開 M:N） |
