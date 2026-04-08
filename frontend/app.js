const canvas = document.getElementById('paintCanvas');
const ctx = canvas.getContext('2d');
const btnClear = document.getElementById('btnClear');
const btnPredict = document.getElementById('btnPredict');
const resultSpan = document.getElementById('digit');
const isLocal = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost';
const BACKEND_URL = isLocal 
    ? 'http://127.0.0.1:8000' 
    : 'https://digit-recognizer-wd8z.onrender.com';

// Cài đặt bút vẽ mô phỏng bút dạ nét to
ctx.lineWidth = 10;
ctx.lineCap = 'round'; // Nét tròn trịa, không bị gãy mép
ctx.strokeStyle = 'black';

// BẮT BUỘC: Tô trắng nền canvas ngay từ đầu. 
// Nếu để nền trong suốt (mặc định), khi xuất file gửi lên model nó sẽ biến thành khối đen thui.
function fillWhiteBackground() {
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
}
fillWhiteBackground();

// Biến trạng thái theo dõi hành vi chuột
let isDrawing = false;

// Các hàm xử lý vẽ
function getPointerPos(e) {
    const rect = canvas.getBoundingClientRect();
    let clientX = e.clientX;
    let clientY = e.clientY;

    // Nếu người dùng dùng màn hình cảm ứng, lấy tọa độ của ngón tay đầu tiên
    if (e.touches && e.touches.length > 0) {
        clientX = e.touches[0].clientX;
        clientY = e.touches[0].clientY;
    }

    return {
        x: clientX - rect.left,
        y: clientY - rect.top
    };
}

// Các hàm xử lý vẽ đã được cập nhật
function startPosition(e) {
    e.preventDefault(); // Chặn thêm một lớp hành vi mặc định của trình duyệt
    isDrawing = true;
    draw(e);
}

function endPosition(e) {
    if (e) e.preventDefault();
    isDrawing = false;
    ctx.beginPath(); 
}

function draw(e) {
    if (!isDrawing) return;
    e.preventDefault(); // Giữ chặt màn hình khi ngón tay đang di chuyển

    const pos = getPointerPos(e);

    ctx.lineTo(pos.x, pos.y);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(pos.x, pos.y);
}

// 1. Lắng nghe sự kiện CHUỘT (Dành cho Laptop/PC)
canvas.addEventListener('mousedown', startPosition);
canvas.addEventListener('mouseup', endPosition);
canvas.addEventListener('mousemove', draw);
canvas.addEventListener('mouseout', endPosition);

// 2. Lắng nghe sự kiện CHẠM (Dành cho Điện thoại/Tablet)
// Phải thêm cờ { passive: false } để trình duyệt cho phép dùng e.preventDefault()
canvas.addEventListener('touchstart', startPosition, { passive: false });
canvas.addEventListener('touchend', endPosition, { passive: false });
canvas.addEventListener('touchmove', draw, { passive: false });
canvas.addEventListener('touchcancel', endPosition, { passive: false });

// Logic nút Xóa
btnClear.addEventListener('click', () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    fillWhiteBackground(); // Bắt buộc tô lại nền trắng sau khi xóa
    resultSpan.innerText = '-';
});

// Logic nút Dự đoán & Nối luồng Backend
btnPredict.addEventListener('click', () => {
    // Đóng gói ảnh thành dạng nhị phân (Blob)
    canvas.toBlob((blob) => {
        const formData = new FormData();
        formData.append('file', blob, 'digit.png'); // Key 'file' phải khớp tuyệt đối với tham số của FastAPI

        // Bắn request lên server
        fetch(`${BACKEND_URL}/predict`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log("Server trả về:", data);
            // Tạm thời hiển thị tên file nhận được từ backend để test luồng
            resultSpan.innerText = data.message; 
        })
        .catch(error => {
            console.error('Lỗi khi gọi API:', error);
            resultSpan.innerText = "Lỗi kết nối Backend!";
        });
    }, 'image/png');
});