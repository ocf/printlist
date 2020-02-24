const RELOAD_TIME = 3000; 

const PrintJob = {
    parse(code) {
        for (let key in PrintJob) {
            if (PrintJob[key].CODE === code) return PrintJob[key];
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


function createElement(tag, classList, attributes, innerText) {
    let currentElement = document.createElement(tag);
    if (classList && !(classList instanceof Array) && typeof classList === 'string') classList = [classList];
    else classList = [];
    if (attributes) {
        if (typeof attributes === 'string') attributes = [attributes]
        if (attributes instanceof Array) {
            attributes.forEach(attribute => currentElement.setAttribute(key, ''));
        } else {
            for (let key in attributes) {
                currentElement.setAttribute(key, attributes[key])
            }
        }
    }
    classList.forEach(className => currentElement.classList.add(className));
    if (innerText) currentElement.innerText = innerText;
    return currentElement;
}

class Job {
    constructor(printer, job) {
        this.printer = printer;
        this.username = job.username;
        this.id = job.id;
        this.last_updated = new Date(job.last_updated*1000);
        this.createEntry();
        this.update(job);
    }
    update(job) {
        this.status = job.status;
        this.last_updated = new Date(job.last_updated*1000);
        let stat = PrintJob.parse(this.status);
        this.entry.status.innerText = stat.MSG;
        this.entry.status.setAttribute('status', stat.ATTR);
    }
    createEntry() {
        this.entry = {
            wrapper: createElement('div', 'printlist-entry'),
            time: createElement(
                'div',
                'time-entry',
                null,
                `${this.last_updated.toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit'
                })}`
            ),
            username: createElement('div', 'username-entry', null, this.username),
            status: createElement('div', 'status-entry')
        };
        this.entry.wrapper.appendChild(this.entry.time);
        this.entry.wrapper.appendChild(this.entry.status);
        this.entry.wrapper.appendChild(this.entry.username);
    }
    clean(time) {
        switch (this.status) {
            case PrintJob.COMPLETED.CODE:
                if (time - this.last_updated.getTime() > window.PERSIST_TIME.COMPLETED)
                    this.remove();
                break;
            case PrintJob.PENDING.CODE:
                if (time - this.last_updated.getTime() > window.PERSIST_TIME.DEFAULT)
                    this.remove();
                break;
            case PrintJob.FILE_ERROR.CODE:
            case PrintJob.QUOTA_LIMIT.CODE:
            case PrintJob.JOB_ERROR.CODE:
            default: 
                if (time - this.last_updated.getTime() > window.PERSIST_TIME.ERROR)
                    this.remove();
        }
    }
    remove() {
        this.printer.jobs.delete(this.id);
        if (this.entry) {
            let targetWrapper = this.entry.wrapper;
            targetWrapper.style.animation = "exit 1s";
            targetWrapper.addEventListener('animationend', ()=>{
                targetWrapper.style.opacity = 0;
                targetWrapper.style.animation = 'exit-post 1s';
                targetWrapper.addEventListener('animationend', ()=>{
                    targetWrapper.remove();
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
            this.nullElement = createElement('div', 'printlist-null', null, '😢 There are no print jobs. 😢');
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
    constructor() {
        this.printers;
        this.last_fetch = 0;
        this.update(this.last_fetch);
        setInterval(() => this.update(this.last_fetch), RELOAD_TIME);
    }
    async update(last_fetch = 0) {
        let fetched = await fetch(`/reload/recent?last-fetch=${last_fetch}`);
        let allPrinters = await fetched.json();
        this.last_fetch = Date.now();
        if (!this.printers) {
            this.printers = {};
            for (let printer_name in allPrinters) 
                this.printers[printer_name] = new Printer(printer_name);
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
(function() {
    fetch('/configuration').then(res => {
        res.json().then(config => {
            for (time in config) {
                config[time] = config[time]*1000;
            }
            console.log('Configuration of persistence time found');
            Object.assign(window, {
                PERSIST_TIME: config
            });
        new AutoReload();
        });
    });
}());
