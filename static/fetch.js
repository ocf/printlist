const RELOAD_TIME = 3000; 
const PERSISTENCE_TIME = 1000;

const PrintJob = {
    COMPLETED: 0,
    PENDING: 1,
    FILE_ERROR: 2,
    QUOTA_LIMIT: 3,
    JOB_ERROR: 4
}

class Job {
    constructor(printer, job) {
        this.printer = printer;
        console.log(job);
        this.last_updated = new Date(job.last_updated*1000);
        this.username = job.username;
        this.id = job.id;
        this.status = job.status;
        this.element = this.createElement();
    }
    update(job) {
        this.status = job.status;
        switch (this.status) {
            case PrintJob.COMPLETED:
                // TODO: Fill out
                break;
            case PrintJob.PENDING:
                // TODO: Fill out
                break;
            case PrintJob.FILE_ERROR:
                // TODO: Fill out
                break;
            case PrintJob.QUOTA_LIMIT:
                // TODO: Fill out
                break;
            case PrintJob.JOB_ERROR:
                // TODO: Fill out
                break;
            default: break;
        }        
    }
    createElement(){
        // TODO : Modify for status codes
        let wrapper = document.createElement('div');
        wrapper.classList.add('printlist-user');
        let name = document.createElement('div');
        name.classList.add('printlist-user-handle');
        name.innerText = this.username;
        wrapper.appendChild(name);
        return wrapper;
    }
    clean(time){
        switch (this.status) {
            case PrintJob.COMPLETED:
                if (time - this.last_updated.getTime() > PERSISTENCE_TIME)
                    this.remove();
                break;
            case PrintJob.PENDING:
                // TODO: Fill out
                break;
            case PrintJob.FILE_ERROR:
                // TODO: Fill out
                break;
            case PrintJob.QUOTA_LIMIT:
                // TODO: Fill out
                break;
            case PrintJob.JOB_ERROR:
                // TODO: Fill out
                break;
            default: break;
        }
    }
    remove(){
        this.printer.jobs.delete(this.id);
        if (this.element) {
            this.element.remove();
            delete this.element;
        }
    }
}

class Printer {
    constructor(printer_name) {
        this.name = printer_name;
        this.reference = document.querySelector(`.${printer_name} h1`);
        this.jobs = new Map();
        this.updateSize();
    }
    clean(currTime) {
        console.log('clean')
        this.jobs.forEach(job => job.clean(currTime));
    }
    updateSize() {
        if (this.jobs.size === 0 && !this.nullElement) {
            this.nullElement = this.createNull();
            console.log(this.reference);
            this.reference.after(this.nullElement);
        } else if (this.jobs.size !== 0) {
            if (this.nullElement) {
                this.nullElement.remove();
                this.nullElement = null;
            }
        }
    }
    addJob(job) {
        if (this.jobs.has(job.id))
            return this.jobs.get(job.id).update();
        let newJob = new Job(this, job);
        this.reference.after(newJob.element);
        return this.jobs.set(job.id, newJob);
    }
    createNull(){
        let nullDiv = document.createElement('div');
        nullDiv.classList.add('printlist-null');
        nullDiv.innerText = '(there are no jobs printing)';
        return nullDiv;        
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
