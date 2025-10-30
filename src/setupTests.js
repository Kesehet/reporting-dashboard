// setupTests.js
import '@testing-library/jest-dom';
import 'jest-canvas-mock';
import { MockServerHandler } from './__test__/mocks/MockServerHandler';
import * as matchers from 'jest-extended';
import fetchMock from "jest-fetch-mock";

fetchMock.enableMocks();

expect.extend(matchers);

MockServerHandler();
