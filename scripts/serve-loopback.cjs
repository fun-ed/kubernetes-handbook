const http = require("node:http");

const originalListen = http.Server.prototype.listen;

// HonKit 6.2.2 has no host option and otherwise binds its preview listeners on
// all interfaces. Its preview and live-reload servers both call listen(port).
http.Server.prototype.listen = function listenLoopbackOnly(port, ...args) {
    const numericPort = typeof port === "number" || (typeof port === "string" && /^\d+$/.test(port));
    if (!numericPort) {
        return originalListen.call(this, port, ...args);
    }

    const supportedArgs = args.filter((argument) =>
        typeof argument === "number" || typeof argument === "function"
    );
    return originalListen.call(this, Number(port), "127.0.0.1", ...supportedArgs);
};
