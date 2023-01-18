/** @odoo-module **/

import SystrayMenu from 'web.SystrayMenu';
import Widget from 'web.Widget';

const core = require('web.core');
var QWeb = core.qweb;


import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const { Component, useState, onWillStart } = owl;

class AircallDialpad extends Component {
    setup() {
        super.setup();
    }
    _onClick(ev) {
        if ($('.iframe_dialpad').hasClass('d-none')){
            $('.iframe_dialpad').removeClass('d-none');
            $('.iframe_dialpad').addClass('show');
        }
        else{
            $('.iframe_dialpad').removeClass('show');
            $('.iframe_dialpad').addClass('d-none');
        }
    }
}
AircallDialpad.template = "aircall_api_integration.AircallDialpad";
export const systrayItem = {
    Component: AircallDialpad,
};
registry.category("systray").add("Dialpad", systrayItem, { sequence: 5 });
