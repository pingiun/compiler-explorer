// Copyright (c) 2018, Patrick Quist
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
//     * Redistributions of source code must retain the above copyright notice,
//       this list of conditions and the following disclaimer.
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
// ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
// LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
// CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
// SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
// INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
// CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
// ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.
"use strict";

const BaseCompiler = require('../base-compiler'),
    logger = require('../logger').logger,
    AsmRaw = require('../asm-raw').AsmParser,
    utils = require('../utils'),
    fs = require("fs-extra"),
    path = require("path"),
    argumentParsers = require("./argument-parsers");

class RunAssemblyCompiler extends BaseCompiler {
    initialise() {
        const compiler = this.compiler.exe;
        const version = '1819';
        logger.debug(`${compiler} is version '${version}'`);
        this.compiler.version = version;
        this.compiler.supportsCfg = this.isCfgCompiler(version);
        this.compiler.supportsAstView = false;
        this.compiler.postProcess = 'dummy';
        return this.getArgumentParser().parse(this);
    }

    getOutputFilename(dirPath) {
        return path.join(dirPath, "output.rom");
    }

    supportsObjdump() {
        return true;
    }

    runCompiler(compiler, options, inputFilename, execOptions) {
        const tmpDir = path.dirname(inputFilename);
        const fileName = path.basename(inputFilename, '.run');

        execOptions = {} //this.getDefaultExecOptions();
        options = [inputFilename];

        return this.exec(compiler, options, execOptions).then(result => {
            return new Promise((resolve) => {
                result.inputFilename = inputFilename;
                result.stdout = utils.parseOutput(result.stdout, inputFilename);
                result.stderr = '';
                
                const aout = path.join(tmpDir, `${fileName}.rom`);
                fs.stat(aout).then(() => {
                    fs.copyFile(aout, this.getOutputFilename(tmpDir)).then(() => {
                        logger.debug(`Copied ${aout} to ${this.getOutputFilename(tmpDir)}`)
                        result.code = 0;
                        resolve(result);
                    });
                }).catch(() => {
                    result.code = 1;
                    resolve(result);
                });
            });
        });
    }

    execPostProcess(result, postProcess, outputFilename, maxSize, options) {
        if (options === undefined) {
            options = [outputFilename];
        }
        return this.exec('./runcpu/disassemble.py', options, {}).then(runresult => {
            return new Promise((resolve) => {
                result.asm = JSON.parse(runresult.stdout);
                resolve(result);
            });
        });
    }

    objdump(outputFilename, result, maxSize, intel, demangle) {
        return this.execPostProcess(result, null, outputFilename, null, [outputFilename, '1']);
    }

    // runCompiler(compiler, options, inputFilename, execOptions) {
    //     if (!execOptions) {
    //         execOptions = this.getDefaultExecOptions();
    //     }
    //     execOptions.customCwd = path.dirname(inputFilename);

    //     return this.exec(compiler, options, execOptions).then(result => {
    //         result.inputFilename = inputFilename;
    //         result.stdout = utils.parseOutput(result.stdout, inputFilename);
    //         result.stderr = utils.parseOutput(result.stderr, inputFilename);
    //         return result;
    //     });
    // }

    // checkOutputFileAndDoPostProcess(asmResult, outputFilename, filters) {
    //     return this.postProcess(asmResult, outputFilename, filters);
    // }

    // getGeneratedOutputfilename(inputFilename) {
    //     const outputFolder = path.dirname(inputFilename);

    //     return new Promise((resolve, reject) => {
    //         fs.readdir(outputFolder, (err, files) => {
    //             files.forEach(file => {
    //                 if (file !== this.compileFilename) {
    //                     resolve(path.join(outputFolder, file));
    //                 }
    //             });
    //             reject("No output file was generated");
    //         });
    //     });
    // }

    // objdump(outputFilename, result, maxSize, intelAsm, demangle) {
    //     return this.getGeneratedOutputfilename(outputFilename).then((realOutputFilename) => {
    //         let args = ["-d", realOutputFilename, "-l", "--insn-width=16"];
    //         if (demangle) args = args.concat("-C");
    //         if (intelAsm) args = args.concat(["-M", "intel"]);
    //         return this.exec(this.compiler.objdumper, args, {maxOutput: maxSize})
    //             .then(objResult => {
    //                 result.asm = objResult.stdout;
    //                 if (objResult.code !== 0) {
    //                     result.asm = "<No output: objdump returned " + objResult.code + ">";
    //                 }
    //                 return result;
    //             });
    //     });
    // }
}


module.exports = RunAssemblyCompiler;
