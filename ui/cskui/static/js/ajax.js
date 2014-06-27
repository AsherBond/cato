// #########################################################################
// #
// # Copyright 2014 Cloud Sidekick
// # __________________
// #
// #  All Rights Reserved.
// #
// # NOTICE:  All information contained herein is, and remains
// # the property of Cloud Sidekick and its suppliers,
// # if any.  The intellectual and technical concepts contained
// # herein are proprietary to Cloud Sidekick
// # and its suppliers and may be covered by U.S. and Foreign Patents,
// # patents in process, and are protected by trade secret or copyright law.
// # Dissemination of this information or reproduction of this material
// # is strictly forbidden unless prior written permission is obtained
// # from Cloud Sidekick.
// #
// #########################################################################

/*
 * This file is used by most pages.  IT contains the specific AJAX calls to get data.
 *
 * The individual pages have code to consume that data as needed.
 *
 */

catoAjax.getPipelines = function(on_success) {"use strict";
    var args = {};
    ajaxPostAsync("/uiMethods/wmGetPipelines", args, on_success);
};

catoAjax.getPipeline = function(pipeline_id, assemble) {"use strict";
    var args = {
        "_id" : pipeline_id,
        "assemble" : assemble
    };
    return ajaxPost("/uiMethods/wmGetPipeline", args);
};

catoAjax.createPipeline = function(template) {"use strict";
    return ajaxPost("/uiMethods/wmCreatePipeline", template);
};

catoAjax.copyPipeline = function(pid, on_success) {"use strict";
    ajaxPostAsync("/uiMethods/wmCopyPipeline", pid, on_success);
};

catoAjax.savePipeline = function(pipeline, on_success) {"use strict";
    ajaxPostAsync("/uiMethods/wmSavePipeline", pipeline, on_success);
};

catoAjax.getPhases = function(filter, include_stages, on_success) {"use strict";
    var args = {
        "filter" : filter,
        "include_stages" : include_stages
    };
    ajaxPostAsync("/uiMethods/wmGetPhases", args, on_success);
};

catoAjax.getPhase = function(phase_id, include_stages) {"use strict";
    var args = {
        "_id" : phase_id,
        "include_stages" : include_stages
    };
    return ajaxPost("/uiMethods/wmGetPhase", args);
};

catoAjax.createPhase = function(template) {"use strict";
    return ajaxPost("/uiMethods/wmCreatePhase", template);
};

catoAjax.copyPhase = function(pid, on_success) {"use strict";
    ajaxPostAsync("/uiMethods/wmCopyPhase", pid, on_success);
};

catoAjax.deletePhase = function(pid, on_success) {"use strict";
    ajaxPostAsync("/uiMethods/wmDeletePhase", pid, on_success);
};

catoAjax.savePhase = function(phase_id, name, stages, on_success) {"use strict";
    var args = {
        "_id" : phase_id,
        "name" : name,
        "stages" : stages
    };
    ajaxPostAsync("/uiMethods/wmSavePhase", args, on_success);
};

catoAjax.getStages = function(filter, on_success) {"use strict";
    var args = {
        "filter" : filter
    };
    ajaxPostAsync("/uiMethods/wmGetStages", args, on_success);
};

catoAjax.getStage = function(stage_id) {"use strict";
    var args = {
        "_id" : stage_id
    };
    return ajaxPost("/uiMethods/wmGetStage", args);
};

catoAjax.createStage = function(template) {"use strict";
    return ajaxPost("/uiMethods/wmCreateStage", template);
};

catoAjax.copyStage = function(sid, on_success) {"use strict";
    ajaxPostAsync("/uiMethods/wmCopyStage", sid, on_success);
};

catoAjax.deleteStage = function(sid, on_success) {"use strict";
    ajaxPostAsync("/uiMethods/wmDeleteStage", sid, on_success);
};

catoAjax.saveStage = function(stage, on_success) {"use strict";
    ajaxPostAsync("/uiMethods/wmSaveStage", stage, on_success);
};

catoAjax.getPlugins = function(filter, on_success) {"use strict";
    var args = {
        "filter" : filter
    };
    ajaxPostAsync("/uiMethods/wmGetPlugins", args, on_success);
};

catoAjax.getPIs = function(pipeline_id, filter) {"use strict";
    var args = {
        "pipeline_id" : pipeline_id,
        "filter" : filter
    };
    return ajaxPost("/uiMethods/wmGetPIs", args);
};

catoAjax.getPI = function(pi_id) {"use strict";
    var args = {
        "_id" : pi_id
    };
    return ajaxPost("/uiMethods/wmGetPI", args);
};

catoAjax.getPIRCs = function(pi_id) {"use strict";
    var args = {
        "pi_id" : pi_id
    };
    return ajaxPost("/uiMethods/wmGetPIRCs", args);
};

catoAjax.getRC = function(rc_id) {"use strict";
    var args = {
        "_id" : rc_id
    };
    return ajaxPost("/uiMethods/wmGetReleaseCandidate", args);
};

catoAjax.getRCPluginSummary = function(rc_id, on_success) {"use strict";
    var args = {
        "rc_id" : rc_id
    };
    ajaxPostAsync("/uiMethods/wmGetRCPluginSummary", args, on_success);
};

catoAjax.getRCLog = function(rc_id, stage, step, on_success) {"use strict";
    var args = {
        "rc_id" : rc_id,
        "stage" : stage,
        "step" : step
    };
    ajaxPostAsync("/uiMethods/wmGetRCLog", args, on_success);
};

catoAjax.updateGate = function(args, on_success) {"use strict";
    ajaxPostAsync("/uiMethods/wmUpdateGate", args, on_success);
};

catoAjax.getPendingGates = function(filter) {"use strict";
    var args = {
        "filter" : filter
    };
    return ajaxPost("/uiMethods/wmGetPendingGates", args);
};

