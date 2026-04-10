const isLocal = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost';
const BACKEND_URL = isLocal ? 'http://127.0.0.1:8000' : 'https://digit-recognizer-wd8z.onrender.com';

// Quản lý UI
const loginArea = document.getElementById('loginArea');
const dashboardArea = document.getElementById('dashboardArea');
const loginError = document.getElementById('loginError');
const tableBody = document.getElementById('tableBody');

// Kiểm tra Token ngay khi tải trang
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('admin_token');
    if (token) {
        showDashboard();
    }
});

// --- LOGIC ĐĂNG NHẬP ---
document.getElementById('btnLogin').addEventListener('click', () => {
    const u = document.getElementById('username').value;
    const p = document.getElementById('password').value;

    // Chú ý: Backend đang dùng Form(...) nên phải gửi dạng x-www-form-urlencoded
    const formData = new URLSearchParams();
    formData.append('username', u);
    formData.append('password', p);

    fetch(`${BACKEND_URL}/admin/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.access_token) {
            localStorage.setItem('admin_token', data.access_token);
            showDashboard();
        } else {
            loginError.innerText = data.error || "Đăng nhập thất bại";
            loginError.style.display = 'block';
        }
    })
    .catch(err => console.error(err));
});

// --- LOGIC ĐĂNG XUẤT ---
document.getElementById('btnLogout').addEventListener('click', () => {
    localStorage.removeItem('admin_token');
    dashboardArea.style.display = 'none';
    loginArea.style.display = 'flex';
});

// --- LOGIC HIỂN THỊ DASHBOARD & LOAD DỮ LIỆU ---
function showDashboard() {
    loginArea.style.display = 'none';
    dashboardArea.style.display = 'block';
    loadFeedbacks();
}

function loadFeedbacks() {
    const token = localStorage.getItem('admin_token');
    
    fetch(`${BACKEND_URL}/admin/feedbacks`, {
        method: 'GET',
        headers: {
            // ĐÂY LÀ CÁCH TRÌNH DIỆN GIẤY THÔNG HÀNH
            'Authorization': `Bearer ${token}` 
        }
    })
    .then(res => {
        if (res.status === 401 || res.status === 403) {
            // Token hết hạn hoặc sai -> Đuổi ra ngoài bắt login lại
            document.getElementById('btnLogout').click();
            throw new Error("Unauthorized");
        }
        return res.json();
    })
    .then(response => {
        if(response.status === 'success') {
            renderTable(response.data);
        }
    })
    .catch(err => console.error("Lỗi load data:", err));
}

// --- LOGIC VẼ BẢNG ---
function renderTable(data) {
    tableBody.innerHTML = ''; // Xóa trắng bảng cũ
    
    if (!data || data.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">Không có dữ liệu chờ duyệt</td></tr>`;
        return;
    }

    data.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>#${item.id}</td>
            <td><img src="${item.image_url}" class="canvas-preview" alt="digit"></td>
            <td><span class="badge bg-secondary fs-6">${item.predicted_label}</span></td>
            <td><span class="badge bg-primary fs-6">${item.actual_label}</span></td>
            <td>${(item.confidence * 100).toFixed(1)}%</td>
            <td>
                <button class="btn btn-sm btn-success me-2" onclick="processFeedback(${item.id}, 'approve')">Duyệt</button>
                <button class="btn btn-sm btn-danger" onclick="processFeedback(${item.id}, 'reject')">Loại</button>
            </td>
        `;
        tableBody.appendChild(tr);
    });
}

// --- LOGIC GỌI API DUYỆT/LOẠI ---
// Tôi để nó ở dạng biến toàn cục để gán thẳng vào onclick trên HTML cho tiện
window.processFeedback = function(id, action) {
    const token = localStorage.getItem('admin_token');
    
    // Gọi API tương ứng (approve hoặc reject)
    fetch(`${BACKEND_URL}/admin/feedbacks/${id}/${action}`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            // Bắn thông báo và Tải lại bảng ngay lập tức để cập nhật UI
            alert(data.message);
            loadFeedbacks(); 
        } else {
            alert("Lỗi: " + data.message);
        }
    });
}