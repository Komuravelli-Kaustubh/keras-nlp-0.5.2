# Copyright 2023 The KerasNLP Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for RoBERTa tokenizer."""

import os

import pytest
import tensorflow as tf
from absl.testing import parameterized
from tensorflow import keras

from keras_nlp.models.roberta.roberta_tokenizer import RobertaTokenizer


class RobertaTokenizerTest(tf.test.TestCase, parameterized.TestCase):
    def setUp(self):
        vocab = {
            "<s>": 0,
            "<pad>": 1,
            "</s>": 2,
            "Ġair": 3,
            "plane": 4,
            "Ġat": 5,
            "port": 6,
            "Ġkoh": 7,
            "li": 8,
            "Ġis": 9,
            "Ġthe": 10,
            "Ġbest": 11,
            "<mask>": 12,
        }

        merges = ["Ġ a", "Ġ t", "Ġ k", "Ġ i", "Ġ b", "Ġa i", "p l", "n e"]
        merges += ["Ġa t", "p o", "r t", "o h", "l i", "Ġi s", "Ġb e", "s t"]
        merges += ["Ġt h", "Ġai r", "pl a", "Ġk oh", "Ġth e", "Ġbe st", "po rt"]
        merges += ["pla ne"]

        self.tokenizer = RobertaTokenizer(vocabulary=vocab, merges=merges)

    def test_tokenize(self):
        input_data = " airplane at airport"
        output = self.tokenizer(input_data)
        self.assertAllEqual(output, [3, 4, 5, 3, 6])

    def test_tokenize_special_tokens(self):
        input_data = "<s> airplane at airport</s><pad>"
        output = self.tokenizer(input_data)
        self.assertAllEqual(output, [0, 3, 4, 5, 3, 6, 0, 1])

    def test_tokenize_batch(self):
        input_data = tf.constant([" airplane at airport", " kohli is the best"])
        output = self.tokenizer(input_data)
        self.assertAllEqual(output, [[3, 4, 5, 3, 6], [7, 8, 9, 10, 11]])

    def test_detokenize(self):
        input_tokens = [[3, 4, 5, 3, 6]]
        output = self.tokenizer.detokenize(input_tokens)
        self.assertAllEqual(output, [" airplane at airport"])

    def test_vocabulary_size(self):
        self.assertEqual(self.tokenizer.vocabulary_size(), 13)

    def test_errors_missing_special_tokens(self):
        with self.assertRaises(ValueError):
            RobertaTokenizer(vocabulary=["a", "b", "c"], merges=[])

    def test_serialization(self):
        config = keras.utils.serialize_keras_object(self.tokenizer)
        new_tokenizer = keras.utils.deserialize_keras_object(config)
        self.assertEqual(
            new_tokenizer.get_config(),
            self.tokenizer.get_config(),
        )

    @parameterized.named_parameters(
        ("tf_format", "tf", "model"),
        ("keras_format", "keras_v3", "model.keras"),
    )
    @pytest.mark.large
    def test_saved_model(self, save_format, filename):
        input_data = tf.constant([" airplane at airport"])

        inputs = keras.Input(dtype="string", shape=())
        outputs = self.tokenizer(inputs)
        model = keras.Model(inputs, outputs)

        path = os.path.join(self.get_temp_dir(), filename)
        # Don't save traces in the tf format, we check compilation elsewhere.
        kwargs = {"save_traces": False} if save_format == "tf" else {}
        model.save(path, save_format=save_format, **kwargs)

        restored_model = keras.models.load_model(path)
        self.assertAllEqual(
            model(input_data),
            restored_model(input_data),
        )
