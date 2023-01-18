/** @odoo-module **/

import AircallPhone from '@aircall_api_integration/js/aircallPhone';
import { PhoneField } from "@web/views/fields/phone/phone_field";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

const phone = new AircallPhone({
  domToLoadPhone: '#phone',
  onLogin: settings => {
    console.log('phone loaded', settings);
  },
  onLogout: () => {
  	console.log('phone logout');
    domToLoadPhone: '#phone'
  }
});

const setPhoneVisibility = visible => {
    const phoneContainer = $('.iframe_dialpad');
    if (visible) {
        phoneContainer.removeClass('d-none');
    } else {
        phoneContainer.addClass('d-none');
    }
};

phone.on('incoming_call', callInfos => {
    setPhoneVisibility(true);
});

patch(PhoneField.prototype, "aircall_api_integration.FormPhoneFieldClick", {
    /**
     * Called when the phone number is clicked.
     *
     * @private
     * @param {MouseEvent} ev
     */
    async onClickCall(ev) {
        if (this.props.value && ev.currentTarget.classList[0] == 'o_phone_form_link') {
            const payload = {
                phone_number: this.props.value
            };
            phone.send(
                'dial_number',
                payload,
                (success, data) => {
                    setPhoneVisibility(true);
                    console.log('success of dial: ', success);
                    console.log('sucess data: ', data);
                }
            );
        }
    },
});
