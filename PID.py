class PIDController():
    def __init__(self, kp, ki, kd, max_output=3.0, max_i=1.0,
                 deriv_tau=0.0, d_clip=None):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.max_output, self.max_i = max_output, max_i
        self.prev_error = 0.0
        self.prev_error2 = 0.0
        self.integral = 0.0
        self.deriv_tau = deriv_tau  # [s], 0.06–0.12 works well at 30 Hz
        self._d_state = 0.0
        self.d_clip = d_clip
        # expose last computed PID components for logging
        self.last_p = 0.0
        self.last_i = 0.0
        self.last_d = 0.0


    def compute(self, error, dt, d_meas=None):
        if dt <= 0: return 0.0
        # I
        self.integral += error * dt
        self.integral = max(-self.max_i, min(self.integral, self.max_i))
        # store I term (ki*integral) for logging
        self.last_i = self.ki * self.integral
        # P term for logging
        self.last_p = self.kp * error
        #Second order backward derivative. If d_meas is provided, it's already a rate.
        raw_d = d_meas if d_meas is not None else (3*error - 4*self.prev_error + self.prev_error2)/ (2*dt)
        # Low-pass filter
        a = self.deriv_tau / (self.deriv_tau + dt)  # 0<a<1
        self._d_state = a*self._d_state + (1.0 - a)*raw_d
        dterm = self.kd * self._d_state
        if self.d_clip is not None:
            dterm = max(-self.d_clip, min(dterm, self.d_clip))
        # store D term (post clipping) for logging
        self.last_d = dterm
        # Sum & clamp
        u = self.last_p + self.last_i + dterm
        self.prev_error2 = self.prev_error
        self.prev_error = error
        
        
        return max(-self.max_output, min(u, self.max_output))

    def reset(self):
        self.prev_error = 0.0
        self.prev_error2 = 0.0
        self.integral = 0.0
        self._d_state = 0.0
