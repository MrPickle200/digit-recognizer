const canvas = document.getElementById('paintCanvas');
const ctx = canvas.getContext('2d');
const btnClear = document.getElementById('btnClear');
const btnPredict = document.getElementById('btnPredict');
const resultSpan = document.getElementById('digit');
const isLocal = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost';
const BACKEND_URL = isLocal 
    ? 'http://127.0.0.1:8000' 
    : 'https://digit-recognizer-wd8z.onrender.com/';

// Cài đặt bút vẽ mô phỏng bút dạ nét to
ctx.lineWidth = 15;
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
function startPosition(e) {
    isDrawing = true;
    draw(e);
}

function endPosition() {
    isDrawing = false;
    ctx.beginPath(); // Ngắt nét cũ để nét mới không bị dính chùm
}

function draw(e) {
    if (!isDrawing) return;

    // Lấy tọa độ chuột tương đối so với bản thân thẻ canvas
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x, y);
}

// Lắng nghe hành vi người dùng
canvas.addEventListener('mousedown', startPosition);
canvas.addEventListener('mouseup', endPosition);
canvas.addEventListener('mousemove', draw);
canvas.addEventListener('mouseout', endPosition); // Đang vẽ mà trượt chuột ra ngoài khung thì ngắt nét ngay

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
        // chay local thi thay url bang cai nay 'http://127.0.0.1:8000'
        fetch('${BACKEND_URL}/predict', {
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