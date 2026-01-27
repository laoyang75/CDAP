/**
 * CDID 数据分析平台前端脚本
 */

// 任务状态轮询
function pollJobStatus(jobId) {
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`/api/jobs/${jobId}`);
            const data = await response.json();

            // 更新进度条
            updateProgress(data.progress, data.progress_message);

            // 更新状态
            updateStatus(data.status);

            // 如果任务完成或失败，停止轮询
            if (data.status === 'completed' || data.status === 'failed') {
                clearInterval(interval);

                if (data.status === 'completed') {
                    showReportReady(jobId);
                } else if (data.status === 'failed') {
                    showError(data.error);
                }
            }
        } catch (error) {
            console.error('轮询任务状态失败:', error);
        }
    }, 3000); // 每3秒轮询一次
}

// 更新进度条
function updateProgress(progress, message) {
    const progressBar = document.querySelector('.progress-bar');
    const progressText = document.querySelector('.progress-text');

    if (progressBar) {
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
        progressBar.textContent = `${progress}%`;
    }

    if (progressText && message) {
        progressText.textContent = message;
    }
}

// 更新状态
function updateStatus(status) {
    const statusBadge = document.querySelector('.status-badge');

    if (!statusBadge) return;

    // 移除所有状态类
    statusBadge.classList.remove('bg-secondary', 'bg-primary', 'bg-info', 'bg-success', 'bg-danger');

    // 根据状态添加对应的类
    const statusMap = {
        'queued': { class: 'bg-secondary', text: '排队中' },
        'fetching_data': { class: 'bg-primary', text: '获取数据中' },
        'analyzing': { class: 'bg-info', text: '分析中' },
        'generating_report': { class: 'bg-info', text: '生成报告中' },
        'completed': { class: 'bg-success', text: '已完成' },
        'failed': { class: 'bg-danger', text: '失败' }
    };

    const statusInfo = statusMap[status] || { class: 'bg-secondary', text: status };
    statusBadge.classList.add(statusInfo.class);
    statusBadge.textContent = statusInfo.text;
}

// 显示报告就绪
function showReportReady(jobId) {
    const reportSection = document.querySelector('.report-section');

    if (reportSection) {
        reportSection.innerHTML = `
            <div class="alert alert-success">
                <h4 class="alert-heading">报告已生成！</h4>
                <p>您的数据分析报告已经生成完成。</p>
                <hr>
                <div class="d-grid gap-2">
                    <a href="/api/jobs/${jobId}/report" class="btn btn-success" target="_blank">
                        <i class="bi bi-download"></i> 下载报告
                    </a>
                </div>
            </div>
        `;
    }
}

// 显示错误
function showError(errorMessage) {
    const errorSection = document.querySelector('.error-section');

    if (errorSection) {
        errorSection.innerHTML = `
            <div class="alert alert-danger">
                <h4 class="alert-heading">任务失败</h4>
                <p>任务处理过程中发生错误：</p>
                <pre>${errorMessage || '未知错误'}</pre>
            </div>
        `;
    }
}

// 文件上传表单处理
document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.querySelector('#uploadForm');

    if (uploadForm) {
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(uploadForm);
            const submitBtn = uploadForm.querySelector('button[type="submit"]');

            // 禁用提交按钮
            submitBtn.disabled = true;
            submitBtn.textContent = '正在提交...';

            try {
                const response = await fetch('/api/jobs', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || '提交失败');
                }

                const data = await response.json();

                // 跳转到任务详情页
                window.location.href = `/tasks/${data.id}`;
            } catch (error) {
                alert(`错误: ${error.message}`);
                submitBtn.disabled = false;
                submitBtn.textContent = '提交任务';
            }
        });
    }
});
