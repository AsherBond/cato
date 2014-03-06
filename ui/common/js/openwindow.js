//Copyright 2014 Cloud Sidekick
//
//Licensed under the Apache License, Version 2.0 (the "License");
//you may not use this file except in compliance with the License.
//You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
//Unless required by applicable law or agreed to in writing, software
//distributed under the License is distributed on an "AS IS" BASIS,
//WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//See the License for the specific language governing permissions and
//limitations under the License.
//

// Utility functions for opening windows consistenly.

//SIZE OF SCREEN FUNCTIONS
function getScreenCenteredTop(eh) {
    var h = screen.height;
    return (h - eh) / 2;
}

function getScreenCenteredLeft(ew) {
    var w = screen.width;
    return (w - ew) / 2;
}

// ------------------------------------------------------------
// These are the window open functions.  They will update a window if one exists with
// the same name.
// openMaxWindow - opens a maximized window.
// openDialogWindow - opens a small dialog window, centered on the screen.
// openWindow - Allows full control of window options.
// TODO...
// Add functions with a _New suffix use a random number
// to ensure that the window name is unique.  This will create a new window every time.

function openMaxWindow(aURL, aWinName) {
    var wOpen;
    var sOptions;

    sOptions = 'status=no,menubar=no,scrollbars=yes,resizable=yes,toolbar=no';
    sOptions = sOptions + ',width=' + screen.width + ',height=' + screen.height + ',top=0,left=0';

    wOpen = window.open(aURL, aWinName, sOptions);
    wOpen.focus();
}

function openDialogWindow(aURL, aWinName, w, h, scroll) {
    var wOpen;
    var sOptions;

    var sc = (scroll === 'yes' || scroll === 'true') ? sc = 'yes' : sc = 'no';
    var t = getScreenCenteredTop(h);
    var l = getScreenCenteredLeft(w);

    sOptions = 'location=no,titlebar=no,status=no,menubar=no,resizable=yes,toolbar=no,scrollbars=' + sc;
    sOptions = sOptions + ',width=' + w + ',height=' + h + ',left=' + l + ',top=' + t;

    wOpen = window.open(aURL, aWinName, sOptions);
    wOpen.focus();
}

function openWindow(URLtoOpen, windowName, windowFeatures) {
    var wOpen = window.open(URLtoOpen, windowName, windowFeatures);
    wOpen.focus();
}
