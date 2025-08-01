/**
 * Recording Calendar Component
 * Calendar widget with recording availability indicators
 * Based on documentation requirements
 */
import playbackService from '../../services/PlaybackService.js';

class RecordingCalendar {
    constructor(container, options = {}) {
        this.container = container;
        this.currentMonth = new Date();
        this.selectedDate = new Date();
        this.recordingDays = new Map(); // day -> recording data
        this.selectedCameraId = null;
        
        this.options = {
            onDateSelect: null,
            onMonthChange: null,
            showWeekNumbers: false,
            highlightToday: true,
            ...options
        };
        
        this.monthNames = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ];
        
        this.dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        
        this.init();
    }
    
    init() {
        this.render();
        this.attachEventListeners();
    }
    
    render() {
        if (!this.container) return;
        
        this.container.innerHTML = this.getTemplate();
        this.updateMonthDisplay();
        this.renderCalendarDays();
    }
    
    getTemplate() {
        return `
            <div class="recording-calendar">
                <div class="calendar-header">
                    <button class="btn btn-sm btn-secondary prev-month" title="Previous Month">
                        <i class="fas fa-chevron-left"></i>
                    </button>
                    <div class="month-year-display">
                        <span class="month-name"></span>
                        <span class="year-name"></span>
                    </div>
                    <button class="btn btn-sm btn-secondary next-month" title="Next Month">
                        <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
                
                <div class="calendar-body">
                    <div class="calendar-weekdays">
                        ${this.dayNames.map(day => `<div class="weekday">${day}</div>`).join('')}
                    </div>
                    <div class="calendar-days">
                        <!-- Days will be rendered here -->
                    </div>
                </div>
                
                <div class="calendar-legend">
                    <div class="legend-item">
                        <div class="legend-indicator has-recordings"></div>
                        <span>Has Recordings</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-indicator partial-recordings"></div>
                        <span>Partial Coverage</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-indicator no-recordings"></div>
                        <span>No Recordings</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-indicator selected-day"></div>
                        <span>Selected</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    attachEventListeners() {
        const prevBtn = this.container.querySelector('.prev-month');
        const nextBtn = this.container.querySelector('.next-month');
        
        prevBtn?.addEventListener('click', () => this.navigateMonth(-1));
        nextBtn?.addEventListener('click', () => this.navigateMonth(1));
        
        // Delegate click events for calendar days
        const calendarDays = this.container.querySelector('.calendar-days');
        calendarDays?.addEventListener('click', (e) => {
            const dayElement = e.target.closest('.calendar-day');
            if (dayElement && !dayElement.classList.contains('other-month')) {
                const day = parseInt(dayElement.dataset.day);
                this.selectDate(day);
            }
        });
    }
    
    async loadMonth(cameraId, year = null, month = null) {
        this.selectedCameraId = cameraId;
        
        if (year !== null && month !== null) {
            this.currentMonth = new Date(year, month - 1, 1);
        }
        
        const currentYear = this.currentMonth.getFullYear();
        const currentMonthNum = this.currentMonth.getMonth() + 1;
        
        try {
            // Fetch calendar data from API
            const calendarData = await playbackService.getCalendarData(
                cameraId, currentYear, currentMonthNum
            );
            
            // Update recording indicators
            this.updateRecordingDays(calendarData.days || {});
            
            // Re-render calendar
            this.updateMonthDisplay();
            this.renderCalendarDays();
            
            // Trigger month change callback
            this.options.onMonthChange?.(currentYear, currentMonthNum, calendarData);
            
        } catch (error) {
            console.error('Failed to load calendar data:', error);
            this.showError('Failed to load calendar data');
        }
    }
    
    updateRecordingDays(daysData) {
        this.recordingDays.clear();
        
        for (const [dayStr, data] of Object.entries(daysData)) {
            const day = parseInt(dayStr);
            
            // Determine recording status based on coverage
            let status = 'no-recordings';
            if (data.has_recordings) {
                if (data.recording_percentage >= 80) {
                    status = 'has-recordings';
                } else if (data.recording_percentage > 0) {
                    status = 'partial-recordings';
                }
            }
            
            this.recordingDays.set(day, {
                ...data,
                status
            });
        }
    }
    
    updateMonthDisplay() {
        const monthNameEl = this.container.querySelector('.month-name');
        const yearNameEl = this.container.querySelector('.year-name');
        
        if (monthNameEl) {
            monthNameEl.textContent = this.monthNames[this.currentMonth.getMonth()];
        }
        
        if (yearNameEl) {
            yearNameEl.textContent = this.currentMonth.getFullYear().toString();
        }
    }
    
    renderCalendarDays() {
        const calendarDays = this.container.querySelector('.calendar-days');
        if (!calendarDays) return;
        
        const year = this.currentMonth.getFullYear();
        const month = this.currentMonth.getMonth();
        
        // Get first day of month and number of days
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const daysInMonth = lastDay.getDate();
        const startDayOfWeek = firstDay.getDay();
        
        // Get days from previous month to fill the grid
        const prevMonth = new Date(year, month - 1, 0);
        const daysInPrevMonth = prevMonth.getDate();
        
        let daysHtml = '';
        
        // Previous month days
        for (let i = startDayOfWeek - 1; i >= 0; i--) {
            const day = daysInPrevMonth - i;
            daysHtml += this.getDayTemplate(day, 'other-month prev-month');
        }
        
        // Current month days
        for (let day = 1; day <= daysInMonth; day++) {
            const classes = [];
            
            // Check if this is today
            const today = new Date();
            const isToday = this.options.highlightToday && 
                           year === today.getFullYear() && 
                           month === today.getMonth() && 
                           day === today.getDate();
            
            if (isToday) classes.push('today');
            
            // Check if this is selected date
            const isSelected = year === this.selectedDate.getFullYear() && 
                              month === this.selectedDate.getMonth() && 
                              day === this.selectedDate.getDate();
            
            if (isSelected) classes.push('selected');
            
            // Check recording status
            const recordingData = this.recordingDays.get(day);
            if (recordingData) {
                classes.push(recordingData.status);
            }
            
            daysHtml += this.getDayTemplate(day, classes.join(' '), recordingData);
        }
        
        // Next month days to fill the grid (ensure 6 weeks)
        const totalCells = 42; // 6 weeks × 7 days
        const cellsUsed = startDayOfWeek + daysInMonth;
        const nextMonthDays = totalCells - cellsUsed;
        
        for (let day = 1; day <= nextMonthDays; day++) {
            daysHtml += this.getDayTemplate(day, 'other-month next-month');
        }
        
        calendarDays.innerHTML = daysHtml;
    }
    
    getDayTemplate(day, classes = '', recordingData = null) {
        const hasRecordings = recordingData && recordingData.has_recordings;
        const coverage = recordingData ? Math.round(recordingData.recording_percentage || 0) : 0;
        const totalSize = recordingData ? playbackService.formatFileSize(recordingData.total_size || 0) : '';
        const duration = recordingData ? playbackService.formatDuration(recordingData.total_duration || 0) : '';
        
        const title = hasRecordings ? 
            `${coverage}% coverage, ${duration} recorded, ${totalSize}` : 
            'No recordings';
        
        return `
            <div class="calendar-day ${classes}" 
                 data-day="${day}" 
                 title="${title}">
                <span class="day-number">${day}</span>
                ${hasRecordings ? `
                    <div class="recording-indicator">
                        <div class="coverage-bar">
                            <div class="coverage-fill" style="width: ${coverage}%"></div>
                        </div>
                        <div class="coverage-text">${coverage}%</div>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    navigateMonth(direction) {
        const newMonth = new Date(this.currentMonth);
        newMonth.setMonth(newMonth.getMonth() + direction);
        this.currentMonth = newMonth;
        
        // Reload data for new month
        if (this.selectedCameraId) {
            this.loadMonth(this.selectedCameraId);
        } else {
            this.updateMonthDisplay();
            this.renderCalendarDays();
        }
    }
    
    selectDate(day) {
        const year = this.currentMonth.getFullYear();
        const month = this.currentMonth.getMonth();
        
        this.selectedDate = new Date(year, month, day);
        
        // Re-render to update selection
        this.renderCalendarDays();
        
        // Trigger callback
        this.options.onDateSelect?.(this.selectedDate, this.recordingDays.get(day));
    }
    
    setSelectedDate(date) {
        this.selectedDate = new Date(date);
        
        // If the selected date is in a different month, navigate to it
        if (date.getFullYear() !== this.currentMonth.getFullYear() || 
            date.getMonth() !== this.currentMonth.getMonth()) {
            
            this.currentMonth = new Date(date.getFullYear(), date.getMonth(), 1);
            
            if (this.selectedCameraId) {
                this.loadMonth(this.selectedCameraId);
            } else {
                this.updateMonthDisplay();
                this.renderCalendarDays();
            }
        } else {
            this.renderCalendarDays();
        }
    }
    
    getSelectedDate() {
        return new Date(this.selectedDate);
    }
    
    getCurrentMonth() {
        return {
            year: this.currentMonth.getFullYear(),
            month: this.currentMonth.getMonth() + 1
        };
    }
    
    getRecordingDataForDay(day) {
        return this.recordingDays.get(day) || null;
    }
    
    showError(message) {
        console.error('RecordingCalendar:', message);
        // You could add visual error indication here
    }
    
    destroy() {
        // Clean up event listeners
        this.container.innerHTML = '';
    }
}

export default RecordingCalendar;