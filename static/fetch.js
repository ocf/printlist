const RELOAD_TIME = 3000; 
const PERSISTENCE_TIME_COMPLETE = 180000;
const PERSISTENCE_TIME_PENDING = 300000;
const PERSISTENCE_TIME_ERROR = 300000;

const PrintJob = {
    PARSE(code) {
        for (let key in PrintJob) {
            if (PrintJob[key].CODE === code) return PrintJob[key]
        }
    },
    COMPLETED: {
        CODE: 0,
        ATTR: 'completed',
        MSG: 'SUCCESS'
    },
    PENDING: {
        CODE: 1,
        ATTR: 'pending',
        MSG: 'PENDING'
    },
    FILE_ERROR: {
        CODE: 2,
        ATTR: 'error',
        MSG: 'FAILURE'
    },
    QUOTA_LIMIT: {
        CODE: 3,
        ATTR: 'error',
        MSG: 'FAILURE'
    },
    JOB_ERROR: {
        CODE: 4,
        ATTR: 'error',
        MSG: 'FAILURE'
    }
}


function _element(tag, classList, attributes, innerText){
    let temp = document.createElement(tag);
    if (classList && !(classList instanceof Array) && typeof classList === 'string') classList = [classList];
    else classList = [];
    if (attributes && attributes instanceof Array) {
        let temp = {};
        attributes.forEach(item => {
            temp[item] = true;
        });
        attributes = temp;
    } else if (attributes && typeof attributes === 'string') {
        attributes = {[attributes]: true}
    } else {
        attributes = {};
    }
    classList.forEach(className => temp.classList.add(className));
    for (let key in attributes) {
        temp.setAttribute(key, attributes[key] && typeof attributes[key] === 'boolean' ? '' : String(attributes[key]));
    }
    if (innerText) temp.innerText = innerText;
    return temp;
}

class Job {
    constructor(printer, job) {
        this.printer = printer;
        this.username = job.username;
        this.id = job.id;
        this.last_updated = new Date(job.last_updated*1000);
        this.createElement();
        this.update(job);
    }
    update(job) {
        this.status = job.status;
        this.last_updated = new Date(job.last_updated*1000);
        let stat = PrintJob.PARSE(this.status);
        this.entry.status.innerText = stat.MSG;
        this.entry.status.setAttribute('status', stat.ATTR);
    }
    getTime() {
        const pad = (str, len) => {
            str = String(str);
            while (str.length < len) str = '0' + str;
            return str;
        }
        let minutes = pad(this.last_updated.getMinutes(), 2);
        let hours = pad(this.last_updated.getHours(), 2);
        let AM = 'AM';
        if (hours >= 13) {
            AM = 'PM';
            hours-=12
        }
        if (hours === 0) hours = 12;
        return `${hours}:${minutes} ${AM}`;
    }
    createElement(){
        this.entry = {
            wrapper: _element('div', 'printlist-entry'),
            time: _element('div', 'time-entry', null, `${this.getTime()}`),
            username: _element('div', 'username-entry', null, this.username),
            status: _element('div', 'status-entry')
        };
        this.entry.wrapper.appendChild(this.entry.time);
        this.entry.wrapper.appendChild(this.entry.status);        
        this.entry.wrapper.appendChild(this.entry.username);
    }
    clean(time){
        const error = () => {
            if (time - this.last_updated.getTime() > PERSISTENCE_TIME_ERROR)
                this.remove();
        }
        switch (this.status) {
            case PrintJob.COMPLETED.CODE:
                if (time - this.last_updated.getTime() > PERSISTENCE_TIME_COMPLETE)
                    this.remove();
                break;
            case PrintJob.PENDING.CODE:
                if (time - this.last_updated.getTime() > PERSISTENCE_TIME_PENDING)
                    this.remove();
                break;
            case PrintJob.FILE_ERROR.CODE:
                error();
                break;
            case PrintJob.QUOTA_LIMIT.CODE:
                error();
                break;
            case PrintJob.JOB_ERROR.CODE:
                error();
                break;
            default: break;
        }
    }
    remove(){
        this.printer.jobs.delete(this.id);
        if (this.entry) {
            let temp = this.entry.wrapper;
            temp.style.animation = "exit 1s";
            temp.addEventListener('animationend', ()=>{
                temp.style.opacity = 0;
                temp.style.animation = 'exit-post 1s';
                temp.addEventListener('animationend', ()=>{
                    temp.remove();
                })
            });
            delete this.entry;
        }
    }
}

class Printer {
    constructor(printer_name) {
        this.name = printer_name;
        this.reference = document.querySelector(`#${printer_name} .printlist`);
        this.jobs = new Map();
        this.updateSize();
    }
    clean(currTime) {
        this.jobs.forEach(job => job.clean(currTime));
    }
    updateSize() {
        if (this.jobs.size === 0 && !this.nullElement) {
            this.nullElement = _element('div', 'printlist-null', null, '\ud83d\ude30 There are no print jobs. \ud83d\ude30');
            this.reference.appendChild(this.nullElement);
        } else if (this.jobs.size !== 0) {
            if (this.nullElement) {
                this.nullElement.remove();
                this.nullElement = null;
            }
        }
    }
    addJob(job) {
        if (this.jobs.has(job.id))
            return this.jobs.get(job.id).update(job);
        let newJob = new Job(this, job);
        if (!this.reference.firstChild) this.reference.appendChild(newJob.entry.wrapper);
        else this.reference.firstChild.before(newJob.entry.wrapper);
        return this.jobs.set(job.id, newJob);
    }
}

class AutoReload {
    constructor(){
        this.printers;
        this.last_fetch = 0;
        this.update(this.last_fetch);
        setInterval(() => this.update(this.last_fetch), RELOAD_TIME);
    }
    async update(last_fetch = 0){
        let fetched = await fetch(`/reload/recent?last-fetch=${last_fetch}`);
        let allPrinters = await fetched.json();
        this.last_fetch = Date.now();
        if (!this.printers) {
            this.printers = {};
            for (let printer_name in allPrinters) this.printers[printer_name] = new Printer(printer_name);
        }
        let currTime = Date.now();

        for (let printer_name in allPrinters) {
            let targetPrinter = this.printers[printer_name];
            allPrinters[printer_name].sort((a, b) => a.time - b.time)
            .forEach(rawJob => targetPrinter.addJob(rawJob));

            targetPrinter.clean(currTime);
            targetPrinter.updateSize();
        }
    }
}
let debug;
(function(){
    debug = new AutoReload();
}());
