import os
import requests
import re
from ruamel.yaml import YAML

# === CẤU HÌNH ===
ORCID_ID = "0009-0004-9174-0289"
CV_FILE = "_data/cv.yml"
BIB_FILE = "_bibliography/papers.bib"
# ================

def clean_text(text):
    """Xóa các khoảng trắng thừa và ký tự lạ"""
    if not text: return ""
    return re.sub(r'\s+', ' ', text).strip()

def pretty_format_bibtex(bib_text, put_code, title):
    """Định dạng lại chuỗi BibTeX cho đẹp và chuẩn hóa Key"""
    if not bib_text: return ""
    
    # Tạo Key sạch sẽ: Ho_Nam_TuKhoa (Ví dụ: Tran_2025_SawMonodetr)
    first_word = re.sub(r'\W+', '', title.split()[0])
    # Tìm năm trong bib_text
    year_match = re.search(r'year\s*=\s*\{?(\d{4})\}?', bib_text)
    year = year_match.group(1) if year_match else "2024"
    new_key = f"Tran_{year}_{first_word}"

    # Phân rã các trường
    # Tìm phần nội dung bên trong @type{key, ...}
    content_match = re.search(r'@[^{]+\{[^,]+,\s*(.*)\}', bib_text, re.DOTALL)
    entry_type_match = re.search(r'@(\w+)', bib_text)
    entry_type = entry_type_match.group(1) if entry_type_match else "article"

    if content_match:
        content = content_match.group(1)
        # Tách các trường dựa trên dấu phẩy nhưng tránh dấu phẩy bên trong ngoặc nhọn
        fields = re.findall(r'(\w+)\s*=\s*(\{.*?\}|"[^"]*"|[^,]+)', content)
        
        pretty_bib = f"@{entry_type}{{{new_key},\n"
        for key, val in fields:
            key = key.strip().lower()
            val = val.strip().rstrip(',')
            pretty_bib += f"  {key:<12} = {val},\n"
        pretty_bib = pretty_bib.rstrip(',\n') + "\n}"
        return pretty_bib
    
    return bib_text # Trả về gốc nếu không parse được

def fetch_orcid_data(orcid_id):
    print(f"🚀 Đang kết nối ORCID API (ID: {orcid_id})...")
    base_url = f"https://pub.orcid.org/v3.0/{orcid_id}"
    headers_json = {'Accept': 'application/json'}
    
    try:
        response = requests.get(f"{base_url}/works", headers=headers_json, timeout=20)
        response.raise_for_status()
        groups = response.json().get('group', [])
        
        formatted_pubs = []
        all_bibtex = []
        
        print(f"📦 Tìm thấy {len(groups)} công trình. Đang làm đẹp dữ liệu...")

        for group in groups:
            work_summary = group.get('work-summary', [{}])[0]
            put_code = work_summary.get('put-code')
            title = clean_text(work_summary.get('title', {}).get('title', {}).get('value', 'Untitled'))
            
            detail_res = requests.get(f"{base_url}/work/{put_code}", headers=headers_json, timeout=15)
            if detail_res.status_code != 200: continue
            detail_data = detail_res.json()
            
            # Lấy BibTeX
            raw_bib = ""
            citation = detail_data.get('citation')
            if citation and citation.get('citation-type', '').lower() == 'bibtex':
                raw_bib = citation.get('citation-value', '').strip()
            
            # Nếu không có, tạo khung cơ bản
            if not raw_bib:
                authors = [c.get('credit-name', {}).get('value') for c in detail_data.get('contributors', {}).get('contributor', []) if c.get('credit-name')]
                author_str = " and ".join(authors) if authors else "Tran, Quan"
                year = work_summary.get('publication-date', {}).get('year', {}).get('value', '2024')
                journal = work_summary.get('journal-title', {}).get('value', 'Journal/Conference')
                raw_bib = f"@article{{tmp,\n  title={{{title}}},\n  author={{{author_str}}},\n  journal={{{journal}}},\n  year={{{year}}}\n}}"

            # Làm đẹp BibTeX
            pretty_bib = pretty_format_bibtex(raw_bib, put_code, title)
            all_bibtex.append(pretty_bib)

            # Data cho CV.yml
            authors_cv = [c.get('credit-name', {}).get('value') for c in detail_data.get('contributors', {}).get('contributor', []) if c.get('credit-name')]
            formatted_pubs.append({
                "title": title,
                "authors": authors_cv if authors_cv else ["Tran, Quan"],
                "publisher": work_summary.get('journal-title', {}).get('value', 'Journal/Conference'),
                "releaseDate": str(work_summary.get('publication-date', {}).get('year', {}).get('value', 'N/A')),
                "summary": f"Source: ORCID"
            })
            print(f"  ✨ Đã xử lý xong: {title[:40]}...")

        formatted_pubs.sort(key=lambda x: x['releaseDate'], reverse=True)
        return formatted_pubs, all_bibtex

    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return [], []

def save_files(new_pubs, bib_entries):
    # --- XỬ LÝ FILE BIBTEX ---
    if bib_entries:
        os.makedirs(os.path.dirname(BIB_FILE), exist_ok=True)
        existing_keys = set()
        
        # Đọc các Key đã tồn tại trong file .bib cũ
        if os.path.exists(BIB_FILE):
            with open(BIB_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                # Regex tìm các key sau dấu @type{KEY,
                existing_keys = set(re.findall(r'@\w+\{([^,]+),', content))

        entries_to_add = []
        for entry in bib_entries:
            # Lấy key của entry mới để so sánh
            match = re.search(r'@\w+\{([^,]+),', entry)
            if match:
                entry_key = match.group(1)
                if entry_key not in existing_keys:
                    entries_to_add.append(entry)
                    existing_keys.add(entry_key) # Tránh trùng ngay trong list mới

        if entries_to_add:
            mode = 'a' if os.path.exists(BIB_FILE) else 'w'
            with open(BIB_FILE, mode, encoding='utf-8') as f:
                if mode == 'a': f.write("\n\n")
                f.write("\n\n".join(entries_to_add))
            print(f"📝 Đã thêm {len(entries_to_add)} bài báo mới vào file BibTeX.")
        else:
            print("ℹ️ Không có bài báo mới nào để thêm vào BibTeX.")

    if new_pubs:
        yaml = YAML()
        yaml.preserve_quotes = True
        if os.path.exists(CV_FILE):
            with open(CV_FILE, 'r', encoding='utf-8') as f:
                data = yaml.load(f)
            data['cv']['sections']['Publications'] = new_pubs
            with open(CV_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(data, f)
            print(f"🎉 Đã cập nhật file CV: {CV_FILE}")

if __name__ == "__main__":
    pubs, bibs = fetch_orcid_data(ORCID_ID)
    save_files(pubs, bibs)