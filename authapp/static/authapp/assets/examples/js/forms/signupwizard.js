(function (global, factory) {
    if (typeof define === "function" && define.amd) {
        define('/forms/wizard', ['jquery', 'Site'], factory);
    } else if (typeof exports !== "undefined") {
        factory(require('jquery'), require('Site'));
    } else {
        var mod = {
            exports: {}
        };
        factory(global.jQuery, global.Site);
        global.formsWizard = mod.exports;
    }
})(this, function (_jquery, _Site) {
    'use strict';

    var _jquery2 = babelHelpers.interopRequireDefault(_jquery);

    (0, _jquery2.default)(document).ready(function ($$$1) {
        (0, _Site.run)();
    });


    // Example Wizard Form Container
    // -----------------------------
    // http://formvalidation.io/api/#is-valid-container
    (function () {
        var defaults = Plugin.getDefaults("wizard");

        var options = _jquery2.default.extend(true, {}, defaults, {
            onInit: function onInit() {
                (0, _jquery2.default)('#exampleFormContainer').formValidation({
                    framework: 'bootstrap',
                    fields: {
                        username: {
                            validators: {
                                notEmpty: {
                                    message: 'The username is required'
                                }
                            }
                        },
                        password: {
                            validators: {
                                notEmpty: {
                                    message: 'The password is required'
                                }
                            }
                        },
                    },
                    err: {
                        clazz: 'invalid-feedback'
                    },
                    control: {
                        // The CSS class for valid control
                        valid: 'is-valid',

                        // The CSS class for invalid control
                        invalid: 'is-invalid'
                    },
                    row: {
                        invalid: 'has-danger'
                    }
                });
            },
            validator: function validator() {
                var fv = (0, _jquery2.default)('#exampleFormContainer').data('formValidation');

                var $this = (0, _jquery2.default)(this);

                // Validate the container
                fv.validateContainer($this);

                var isValidStep = fv.isValidContainer($this);
                if (isValidStep === false || isValidStep === null) {
                    return false;
                }
                if ($('#uname_response').html() === '' || $('#uname_response').html() === '<span id="resp" style="color: green;">Available.</span>') {
                    console.log('true')
                    return true;
                }else {
                    console.log('false')
                    return false;
                }

                return true;
            },
            onFinish: function onFinish() {
                console.log( $('#exampleFormContainer')[0])
                $('#exampleFormContainer')[0].submit();
            },
            buttonsAppendTo: '.panel-body'
        });

        (0, _jquery2.default)("#exampleWizardFormContainer").wizard(options);
    })();

});