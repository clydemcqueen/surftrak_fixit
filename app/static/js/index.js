// Overall status
let el_sts_extension_down = document.getElementById("sts_extension_down");
let el_sts_sub_down = document.getElementById("sts_sub_down");
let el_sts_reboot_required = document.getElementById("sts_reboot_required");
let el_sts_waiting_for_reboot = document.getElementById("sts_waiting_for_reboot");

// MAVLink sensors
let el_sensor_ping = document.getElementById("sensor_ping");
let el_sensor_wl_dvl= document.getElementById("sensor_wl_dvl");

// Timeouts
let el_prb_rangefinder_timeout = document.getElementById("prb_rangefinder_timeout");
let el_prb_global_position_int_timeout = document.getElementById("prb_global_position_int_timeout");

// Errors
let el_prb_no_sensor_msgs = document.getElementById("prb_no_sensor_msgs");
let el_prb_too_many_sensor_msgs = document.getElementById("prb_too_many_sensor_msgs");
let el_prb_bad_type = document.getElementById("prb_bad_type");
let el_prb_bad_orient = document.getElementById("prb_bad_orient");

// Warnings
let el_prb_bad_max = document.getElementById("prb_bad_max");
let el_prb_bad_max_msg = document.getElementById("prb_bad_max_msg");
let el_prb_bad_kpv = document.getElementById("prb_bad_kpv");
let el_prb_bad_kpv_msg = document.getElementById("prb_bad_kpv_msg");
let el_prb_no_btn = document.getElementById("prb_no_btn");

// ArduSub state
let el_ardusub_version_card = document.getElementById("ardusub_version_card");
let el_relative_alt_m_card = document.getElementById("relative_alt_m_card");
let el_rf_target_m_card = document.getElementById("rf_target_m_card");
let el_rangefinder_m_card = document.getElementById("rangefinder_m_card");
let el_seafloor_alt_m_card = document.getElementById("seafloor_alt_m_card");

// Parameter values
let el_rngfnd1_type_card = document.getElementById("rngfnd1_type_card");
let el_rngfnd1_min_label = document.getElementById("rngfnd1_min_label");
let el_rngfnd1_max_label = document.getElementById("rngfnd1_max_label");
let el_rngfnd1_min_card = document.getElementById("rngfnd1_min_card");
let el_rngfnd1_max_card = document.getElementById("rngfnd1_max_card");
let el_rngfnd1_orient_card = document.getElementById("rngfnd1_orient_card");
let el_psc_jerk_z_label = document.getElementById("psc_jerk_z_label");
let el_psc_jerk_z_card = document.getElementById("psc_jerk_z_card");
let el_pilot_accel_z_label = document.getElementById("pilot_accel_z_label");
let el_pilot_accel_z_card = document.getElementById("pilot_accel_z_card");
let el_surftrak_depth_card = document.getElementById("surftrak_depth_card");
let el_rngfnd_sq_min_card = document.getElementById("rngfnd_sq_min_card");
let el_btn_surftrak_card = document.getElementById("btn_surftrak_card");

const default_json = {
    "mav_state" : -1,  // -1 means BE is down, 0-2 are from the BE
    "reboot_required" : false,
    "vehicle_version" : null,
    "ping" : null,
    "wl_dvl" : null,
    "prb_rangefinder_timeout" : false,
    "prb_global_position_int_timeout" : false,
    "relative_alt_m" : null,
    "rf_target_m" : null,
    "rangefinder_m" : null,
    "rngfnd1_type" : null,
    "rngfnd1_min" : null,
    "rngfnd1_max" : null,
    "rngfnd1_min_cm" : null,
    "rngfnd1_max_cm" : null,
    "rngfnd1_orient" : null,
    "surftrak_depth" : null,
    "psc_jerk_z" : null,
    "pilot_accel_z" : null,
    "rngfnd_sq_min" : null,
    "btn_surftrak" : null,
}

function formatNumber(val, decimals = 3) {
    if (val === null || val === undefined) {
        return "Unknown";
    }
    if (typeof val === "number") {
        return parseFloat(val.toFixed(decimals)).toString();
    }
    return val.toString();
}

async function getStatus() {
    let response_json = default_json;

    // Get the latest status
    try {
        const response = await fetch("/status");
        if (response.ok) {
            response_json = await response.json();
        }
    } catch (ex) {
        console.error(ex)
    }

    const {
        mav_state,
        reboot_required,
        vehicle_version,
        ping,
        wl_dvl,
        prb_rangefinder_timeout,
        prb_global_position_int_timeout,
        relative_alt_m,
        rf_target_m,
        rangefinder_m,
        rngfnd1_type,
        rngfnd1_min,
        rngfnd1_max,
        rngfnd1_min_cm,
        rngfnd1_max_cm,
        rngfnd1_orient,
        surftrak_depth,
        psc_jerk_z,
        pilot_accel_z,
        rngfnd_sq_min,
        btn_surftrak,
    } = response_json;

    // Overall status
    el_sts_extension_down.className = mav_state === -1 ? "status-shown" : "status-hidden";
    el_sts_sub_down.className = mav_state === 0 ? "status-shown" : "status-hidden";
    el_sts_reboot_required.className = reboot_required ? "status-shown" : "status-hidden";
    el_sts_waiting_for_reboot.className = mav_state === 2 ? "status-shown" : "status-hidden";

    // MAVLink sensors
    let num_sensors = 0;
    if (ping) {
        document.getElementById("ping_distance").textContent = (ping['distance'] * 0.01).toFixed(2);
        document.getElementById("ping_sq").textContent = (ping['sq']).toString();
        el_sensor_ping.className = "status-shown";
        ++num_sensors;
    } else {
        el_sensor_ping.className = "status-hidden";
    }
    if (wl_dvl) {
        document.getElementById("wl_dvl_distance").textContent = (wl_dvl['distance'] * 0.01).toFixed(2);
        document.getElementById("wl_dvl_sq").textContent = (wl_dvl['sq']).toString();
        el_sensor_wl_dvl.className = "status-shown";
        ++num_sensors;
    } else {
        el_sensor_wl_dvl.className = "status-hidden";
    }

    // Calc kpv, see https://github.com/clydemcqueen/ardusub_surftrak/ for definition
    let kpv = psc_jerk_z === null || pilot_accel_z === null ? 0 : 50 * psc_jerk_z / pilot_accel_z;

    // Timeouts
    el_prb_rangefinder_timeout.className = mav_state === 1 && prb_rangefinder_timeout ? "status-shown" : "status-hidden";
    el_prb_global_position_int_timeout.className = mav_state === 1 && prb_global_position_int_timeout ? "status-shown" : "status-hidden";

    // Errors
    el_prb_no_sensor_msgs.className = rngfnd1_type === 10 && num_sensors === 0 ? "status-shown" : "status-hidden";
    el_prb_too_many_sensor_msgs.className = rngfnd1_type === 10 && num_sensors > 1 ? "status-shown" : "status-hidden";
    el_prb_bad_type.className = rngfnd1_type === 0 || (rngfnd1_type !== 10 && num_sensors > 0) ? "status-shown" : "status-hidden";
    el_prb_bad_orient.className = rngfnd1_orient !== null && rngfnd1_orient !== 25 ? "status-shown" : "status-hidden";

    // Warnings
    if (vehicle_version === "4.7") {
        if (el_prb_bad_max_msg) {
            el_prb_bad_max_msg.textContent = "RNGFND1_MAX is 7m, did you mean 50m?";
        }
        if (el_prb_bad_kpv_msg) {
            el_prb_bad_kpv_msg.textContent = "To reduce oscillation, set PSC_D_JERK to 8 and PILOT_ACC_Z to 500";
        }
        el_prb_bad_max.className = rngfnd1_type !== null && rngfnd1_type !== 0 && (rngfnd1_max !== null && Math.abs(rngfnd1_max - 7.0) < 0.01) ? "status-shown" : "status-hidden";
    } else {
        if (el_prb_bad_max_msg) {
            el_prb_bad_max_msg.textContent = "RNGFND1_MAX_CM is 700cm, did you mean 5000cm?";
        }
        if (el_prb_bad_kpv_msg) {
            el_prb_bad_kpv_msg.textContent = "To reduce oscillation, set PSC_JERK_Z to 8 and PILOT_ACCEL_Z to 500";
        }
        let max_val = rngfnd1_max_cm !== null ? rngfnd1_max_cm : rngfnd1_max;
        el_prb_bad_max.className = rngfnd1_type !== null && rngfnd1_type !== 0 && (max_val !== null && Math.abs(max_val - 700) < 1.0) ? "status-shown" : "status-hidden";
    }
    el_prb_bad_kpv.className = kpv > 1.0 ? "status-shown" : "status-hidden";
    el_prb_no_btn.className = mav_state === 1 && btn_surftrak === null ? "status-shown" : "status-hidden";

    // ArduSub state
    if (el_ardusub_version_card) {
        el_ardusub_version_card.textContent = vehicle_version != null ? ("ArduSub " + vehicle_version) : "Unknown";
    }
    el_relative_alt_m_card.textContent = relative_alt_m != null ? relative_alt_m.toFixed(2) : "Unknown";
    el_rf_target_m_card.textContent = rf_target_m != null && rf_target_m > 0 ? rf_target_m.toFixed(2) : "No target";
    el_rangefinder_m_card.textContent = rangefinder_m != null ? rangefinder_m.toFixed(2) : "No rangefinder";
    el_seafloor_alt_m_card.textContent = relative_alt_m != null && rangefinder_m != null ? (relative_alt_m - rangefinder_m).toFixed(2) : "Unknown";

    // Parameter values
    el_rngfnd1_type_card.textContent = formatNumber(rngfnd1_type);

    if (vehicle_version === "4.7") {
        if (el_rngfnd1_min_label) el_rngfnd1_min_label.textContent = "RNGFND1_MIN (m)";
        if (el_rngfnd1_max_label) el_rngfnd1_max_label.textContent = "RNGFND1_MAX (m)";
        if (el_psc_jerk_z_label) el_psc_jerk_z_label.textContent = "PSC_D_JERK (m/s^3)";
        if (el_pilot_accel_z_label) el_pilot_accel_z_label.textContent = "PILOT_ACC_Z (cm/s^2)";
        el_rngfnd1_min_card.textContent = formatNumber(rngfnd1_min);
        el_rngfnd1_max_card.textContent = formatNumber(rngfnd1_max);
    } else {
        if (el_rngfnd1_min_label) el_rngfnd1_min_label.textContent = "RNGFND1_MIN_CM (cm)";
        if (el_rngfnd1_max_label) el_rngfnd1_max_label.textContent = "RNGFND1_MAX_CM (cm)";
        if (el_psc_jerk_z_label) el_psc_jerk_z_label.textContent = "PSC_JERK_Z (cm/s^3)";
        if (el_pilot_accel_z_label) el_pilot_accel_z_label.textContent = "PILOT_ACCEL_Z (cm/s^2)";
        let min_val = rngfnd1_min_cm !== null ? rngfnd1_min_cm : rngfnd1_min;
        let max_val = rngfnd1_max_cm !== null ? rngfnd1_max_cm : rngfnd1_max;
        el_rngfnd1_min_card.textContent = formatNumber(min_val);
        el_rngfnd1_max_card.textContent = formatNumber(max_val);
    }

    el_rngfnd1_orient_card.textContent = formatNumber(rngfnd1_orient);
    el_surftrak_depth_card.textContent = formatNumber(surftrak_depth);
    el_psc_jerk_z_card.textContent = formatNumber(psc_jerk_z);
    el_pilot_accel_z_card.textContent = formatNumber(pilot_accel_z);
    el_rngfnd_sq_min_card.textContent = formatNumber(rngfnd_sq_min);
    el_btn_surftrak_card.textContent = btn_surftrak === null ? "No assignment" : btn_surftrak;
}

setInterval(getStatus, 500);

async function postFixit(fix) {
    try {
        const response = await fetch("/fixit", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({fix: fix}),
        });

        // TODO report result
        const result = await response.json();
    } catch (ex) {
        console.error(ex);
    }
}
